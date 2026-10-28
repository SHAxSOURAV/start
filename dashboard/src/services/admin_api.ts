import axios from "axios";
import { ApiResponse, ManageStatusPayload, UserSummary } from "@/types";

const ADMIN_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const adminClient = axios.create({
  baseURL: ADMIN_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const setAdminToken = (token: string | null) => {
  if (token) {
    adminClient.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete adminClient.defaults.headers.common["Authorization"];
  }
};

export const adminUserService = {
  getUsers: async (page = 1, limit = 20) => {
    const res = await adminClient.get<ApiResponse<UserSummary[]>>(`/admin/users?page=${page}&limit=${limit}`);
    return res.data;
  },

  manageUserStatus: async (userId: string, payload: ManageStatusPayload) => {
    const res = await adminClient.patch<ApiResponse<UserSummary>>(`/admin/users/${userId}/status`, payload);
    return res.data;
  },
};
