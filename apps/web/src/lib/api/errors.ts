export interface ApiErrorData {
  code?: string;
  message: string;
  requestId?: string;
  retryAfter?: number;
}

export class ApiError extends Error {
  public readonly status: number;
  public readonly code?: string;
  public readonly requestId?: string;
  public readonly retryAfter?: number;

  constructor(status: number, data: ApiErrorData | string) {
    if (typeof data === "string") {
      super(data);
      this.status = status;
    } else {
      super(data.message);
      this.status = status;
      this.code = data.code;
      this.requestId = data.requestId;
      this.retryAfter = data.retryAfter;
    }
    this.name = "ApiError";
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

