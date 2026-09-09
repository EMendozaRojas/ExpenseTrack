export interface Category {
  id: number;
  name: string;
  owner_id: number | null;
  parent_id: number | null;
  kind: "income" | "expense";
  icon: string | null;
  color: string | null;
  is_system: boolean;
  is_fixed: boolean;
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

export type NetStatus = "a_favor" | "en_contra";

export interface DashboardCategoryNode {
  category_id: number;
  category_name: string;
  icon: string | null;
  color: string | null;
  total: string;
  subcategories: CategorySummary[];
}

export type BudgetStatusValue = "ok" | "warning" | "exceeded";

export interface Budget {
  id: number;
  category_id: number;
  category_name: string;
  amount: string;
  is_active: boolean;
  created_at: string;
}

export interface BudgetWithStatus {
  id: number;
  category_id: number;
  category_name: string;
  category_icon: string | null;
  amount: string;
  is_active: boolean;
  spent: string;
  pct: number;
  status: BudgetStatusValue;
}

export interface BudgetInput {
  category_id: number;
  amount: string;
}

export type ImportClassification = "NEW" | "EXACT_DUPLICATE" | "PROBABLE_DUPLICATE";
export type ImportStrategy = "append_new" | "replace_range" | "replace_selected";

export interface ImportRow {
  id: number;
  posted_at: string;
  amount: string;
  raw_description: string;
  classification: ImportClassification;
  matched_transaction_id: number | null;
}

export interface ImportPreview {
  id: number;
  account_id: number;
  filename: string;
  status: string;
  range_start: string;
  range_end: string;
  created_at: string;
  new_count: number;
  exact_duplicate_count: number;
  probable_duplicate_count: number;
  rows: ImportRow[];
}

export interface ImportCommitResult {
  id: number;
  status: string;
  strategy: ImportStrategy;
  inserted_count: number;
  replaced_count: number;
  skipped_count: number;
}

export interface DashboardSummary {
  year: number;
  month: number;
  income_total: string;
  expense_total: string;
  net_total: string;
  net_status: NetStatus;
  fixed_total: string;
  variable_total: string;
  by_category: DashboardCategoryNode[];
  incomplete_data: boolean;
  last_transaction_date: string | null;
}
