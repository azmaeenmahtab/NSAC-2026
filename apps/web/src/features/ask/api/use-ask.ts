import { useMutation } from "@tanstack/react-query";
import { apiPost, type ApiResponse } from "@/lib/api/client";
import type { AskRequest, AskResponse } from "../types";

export function useAsk() {
  return useMutation<ApiResponse<AskResponse>, Error, AskRequest>({
    mutationFn: (req: AskRequest) =>
      apiPost<ApiResponse<AskResponse>>("/ask", req),
  });
}
