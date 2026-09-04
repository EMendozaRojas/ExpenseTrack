export interface Category {
  id: number;
  name: string;
  owner_id: number | null;
  parent_id: number | null;
  kind: "income" | "expense";
  icon: string | null;
  color: string | null;
  is_system: boolean;
  created_at: string;
  children: Category[];
}

export type AccountType = "checking" | "savings" | "credit_card" | "cash" | "wallet";

export interface Account {
  id: number;
  owner_id: number;
  name: string;
  type: AccountType;
  currency: string;
  initial_balance: string;
  balance: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountInput {
  name: string;
  type: AccountType;
  currency?: string;
  initial_balance?: string;
}

export type Direction = "income" | "expense" | "transfer";

export interface Transaction {
  id: number;
  account_id: number;
  owner_id: number;
  amount: string;
  direction: Direction;
  posted_at: string;
  category_id: number | null;
  counterparty: string | null;
  raw_description: string | null;
  note: string | null;
  source: "manual" | "import" | "rule";
  transfer_group_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface TransactionInput {
  account_id: number;
  amount: string;
  direction: "income" | "expense";
  posted_at: string;
  category_id: number | null;
  note: string | null;
}

export interface TransactionPage {
  items: Transaction[];
  next_cursor: string | null;
}

export interface CategorySummary {
  category_id: number;
  category_name: string;
  total: string;
}

export interface MonthlySummary {
  year: number;
  month: number;
  total: string;
  by_category: CategorySummary[];
}
