import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, throwError } from 'rxjs';

import { environment } from '../../environments/environment';
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
    return this.http
      .post<AnalyzeResponse>(environment.analyzeUrl, { text })
      .pipe(catchError((e: HttpErrorResponse) => throwError(() => toApiError(e))));
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
