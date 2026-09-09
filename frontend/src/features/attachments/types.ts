export interface Attachment {
  id: number;
  transaction_id: number;
  filename: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
}
