import { useMutation } from "@tanstack/react-query";
import { apiPostData } from "@/lib/api/client";
import type { SubscriptionPayload, SubscriptionResponse } from "../types";

export function useSubscribe() {
  return useMutation<SubscriptionResponse, Error, SubscriptionPayload>({
    mutationFn: async (payload: SubscriptionPayload) => {
      const data = await apiPostData<SubscriptionResponse>(
        "/alerts/subscriptions",
        payload
      );
      return data;
    },
  });
}

