export interface ApiResponse<T = unknown> {
  statusCode: number;
  success: boolean;
  message: string;
  data: T;
  meta?: {
    page?: number;
    limit?: number;
    total?: number;
    totalPage?: number;
  };
}

export type AccountStatus = "ACTIVE" | "BLOCKED" | "SUSPENDED" | "INACTIVE";
export type UserRole = "USER" | "DRIVER" | "ADMIN" | "SUPER_ADMIN";

export interface UserSummary {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: AccountStatus;
  createdAt: string;
}

export interface ManageStatusPayload {
  action: "ACTIVATE" | "SUSPEND" | "BAN";
  reason: string;
  duration_hours?: number;
  revoke_sessions?: boolean;
  notify_user?: boolean;
}
