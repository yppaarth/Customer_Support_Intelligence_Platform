export type TicketListItem = {
  id: string;
  subject: string;
  status: string;
  priority: string;
  ai_confidence: number | null;
  created_at: string;
  updated_at: string;
  customer_name: string | null;
  issue_category: string | null;
  assigned_agent: string | null;
  escalated: boolean;
};

export type Page<T> = { items: T[]; total: number; limit: number; offset: number };

export type TicketDetail = {
  id: string;
  subject: string;
  status: string;
  priority: string;
  ai_confidence: number | null;
  customer: { id: string; name: string; email: string; tier: string } | null;
  order_context: Array<{ order_number: string; status: string; total_amount: number }>;
  messages: Array<{ id: string; sender_type: string; sender_name: string | null; body: string; created_at: string }>;
  classification: null | {
    issue_category: string;
    sentiment: string;
    requires_human_review: boolean;
    risk_flags: string[];
    summary: string;
    confidence: number;
  };
  latest_draft: null | {
    id: string;
    body: string;
    status: string;
    confidence: number;
    risk_flags: string[];
    quality: Record<string, unknown>;
    citations: Array<{ id: string; title: string; section: string | null; page_number: number | null; quote: string; is_valid: boolean }>;
  };
  escalations: Array<{ id: string; reason: string; priority: string; status: string }>;
  audit: Array<{ action: string; created_at: string }>;
};
