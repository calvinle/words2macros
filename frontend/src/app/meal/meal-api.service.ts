import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, map, throwError } from 'rxjs';

import { environment } from '../../environments/environment';
import { validateAnalyzeResponse } from './meal-validation';
import { AnalyzeResponse } from './meal.models';

/** Every failure from analyze() arrives in this one shape. */
export class ApiError {
  constructor(
    readonly code: string,
    readonly message: string,
    readonly requestId?: string,
  ) {}
}

/** The only code that talks to the backend. */
@Injectable({ providedIn: 'root' })
export class MealApiService {
  private http = inject(HttpClient);

  analyze(text: string): Observable<AnalyzeResponse> {
    return this.http.post<unknown>(environment.analyzeUrl, { text }).pipe(
      catchError((e: HttpErrorResponse) => throwError(() => toApiError(e))),
      map(checked),
    );
  }
}

/** Never pass unvalidated data on, even from our own backend. */
function checked(body: unknown): AnalyzeResponse {
  try {
    return validateAnalyzeResponse(body);
  } catch (e) {
    console.error('words2macros: /analyze response failed validation', e, body);
    const requestId = (body as { request_id?: string } | null)?.request_id;
    throw new ApiError(
      'INVALID_RESPONSE',
      'The server sent a result in an unexpected format, so it was not shown. Try again.',
      typeof requestId === 'string' ? requestId : undefined,
    );
  }
}

function toApiError(e: HttpErrorResponse): ApiError {
  // The backend's own errors: { error: { code, message, request_id } }
  const body = e.error?.error;
  if (body?.code && body?.message) {
    return new ApiError(body.code, body.message, body.request_id);
  }
  // Responses that never reached the Lambda: no network, the API Gateway
  // throttle, or the kill switch (API Gateway answers with a generic error).
  if (e.status === 0) {
    return new ApiError(
      'NETWORK',
      'The server could not be reached. Check the connection and try again.',
    );
  }
  if (e.status === 429) {
    return new ApiError('THROTTLED', 'The demo is busy. Try again in a minute.');
  }
  return new ApiError('UNAVAILABLE', 'The demo is unavailable right now. Try again later.');
}
