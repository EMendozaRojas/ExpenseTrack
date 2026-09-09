export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface Credentials {
  email: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  refresh_token?: string | null;
}
