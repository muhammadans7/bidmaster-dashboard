import { apiClient } from "../api/client";

export async function fetchAuctionState() {
  const response = await apiClient.get("/auction/state");
  return response.data;
}

export async function submitBid(teamName, amount) {
  const response = await apiClient.post("/auction/bid", {
    team_name: teamName,
    amount,
  });
  return response.data;
}

export async function closeAuction() {
  const response = await apiClient.post("/auction/close");
  return response.data;
}

export async function resetAuction() {
  const response = await apiClient.post("/auction/reset");
  return response.data;
}
