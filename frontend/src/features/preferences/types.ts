export interface UserPreferences {
  base_currency: string;
  locale: string;
  has_transactions: boolean;
}

export interface UserPreferencesUpdate {
  base_currency?: string;
  locale?: string;
}
