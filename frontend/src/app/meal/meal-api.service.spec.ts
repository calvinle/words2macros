import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../environments/environment';
import { ApiError, MealApiService } from './meal-api.service';
import { AnalyzeResponse } from './meal.models';

const MEAL: AnalyzeResponse = {
  items: [
    {
      name: 'gravy',
      preparation: null,
      grams: 60,
      amount_source: 'estimated',
      assumption: '1 serving (1/4 cup)',
      match: {
        source: 'usda',
        fdc_id: 123,
        description: 'Gravy, turkey, canned',
        per_100g: { calories_kcal: 51, protein_g: 2.6, carbs_g: 5.1, fat_g: 2.1 },
      },
      nutrients: { calories_kcal: 30.6, protein_g: 1.56, carbs_g: 3.06, fat_g: 1.26 },
    },
  ],
  totals: { calories_kcal: 30.6, protein_g: 1.56, carbs_g: 3.06, fat_g: 1.26 },
  warnings: [],
  text: 'a serving of gravy',
  request_id: 'req-1',
  analyzed_at: '2026-10-11T00:00:00Z',
};

describe('MealApiService', () => {
  let service: MealApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(MealApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  /** Calls analyze(), answers the request with `respond`, returns the error. */
  function errorFor(respond: (req: ReturnType<HttpTestingController['expectOne']>) => void) {
    let error: ApiError | undefined;
    service.analyze('anything').subscribe({ error: (e) => (error = e) });
    respond(http.expectOne(environment.analyzeUrl));
    return error;
  }

  it('posts the text and passes a success response through', () => {
    let result: AnalyzeResponse | undefined;
    service.analyze('a serving of gravy').subscribe((r) => (result = r));

    const req = http.expectOne(environment.analyzeUrl);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ text: 'a serving of gravy' });
    req.flush(MEAL);

    expect(result).toEqual(MEAL);
  });

  it("maps the backend's error body to its code and message", () => {
    const error = errorFor((req) =>
      req.flush(
        { error: { code: 'TOO_MANY_FOODS', message: 'Too many.', request_id: 'req-2' } },
        { status: 422, statusText: 'Unprocessable Entity' },
      ),
    );
    expect(error).toEqual(new ApiError('TOO_MANY_FOODS', 'Too many.', 'req-2'));
  });

  it('maps the API Gateway throttle (429) to THROTTLED', () => {
    const error = errorFor((req) =>
      req.flush({ message: 'Too Many Requests' }, { status: 429, statusText: 'Too Many Requests' }),
    );
    expect(error?.code).toBe('THROTTLED');
  });

  it('maps a network failure (status 0) to NETWORK', () => {
    const error = errorFor((req) => req.error(new ProgressEvent('error')));
    expect(error?.code).toBe('NETWORK');
  });

  it('maps an unknown 5xx (e.g. the kill switch) to UNAVAILABLE', () => {
    const error = errorFor((req) =>
      req.flush(
        { message: 'Internal Server Error' },
        { status: 500, statusText: 'Internal Server Error' },
      ),
    );
    expect(error?.code).toBe('UNAVAILABLE');
  });
});
