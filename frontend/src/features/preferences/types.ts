export interface UserPreferences {
  base_currency: string;
  locale: string;
}

export interface UserPreferencesUpdate {
  base_currency?: string;
  locale?: string;
}
