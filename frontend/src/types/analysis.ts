export type AnalysisType = 'comprehensive' | 'liquidity' | 'profitability' | 'leverage' | 'quick';

export type MetricStatus = 'good' | 'warning' | 'poor';

export interface Citation {
  page: number;
  document_name: string;
  document_id: string;
}

export interface FinancialMetric {
  name: string;
  value: number;
  formatted_value: string;
  category: 'liquidity' | 'profitability' | 'leverage';
  citations: Citation[];
  interpretation?: {
    status: MetricStatus;
    text: string;
  };
}

export interface AIInsight {
  category: 'risk_assessment' | 'liquidity_position' | 'financial_health' | 'recommendations';
  title: string;
  content: string;
  supporting_metrics?: string[];
  citations?: Citation[];
  severity?: 'low' | 'medium' | 'high';
}

export interface AnalysisResult {
  id: string;
  document_id: string;
  analysis_type: AnalysisType;
  quality_score: number;
  metrics: FinancialMetric[];
  insights: AIInsight[];
  created_at: string;
  updated_at: string;
  cached: boolean;
}

export interface SemanticSearchResult {
  chunk_id: string;
  document_id: string;
  page_num: number;
  text: string;
  score: number;
  context?: {
    before: Array<{
      chunk_id: string;
      page_num: number;
      chunk_idx: number;
      text: string;
      char_count: number;
      word_count: number;
    }>;
    after: Array<{
      chunk_id: string;
      page_num: number;
      chunk_idx: number;
      text: string;
      char_count: number;
      word_count: number;
    }>;
  };
}

export interface SemanticSearchResponse {
  query: string;
  results: SemanticSearchResult[];
  total_count: number;
}

// Metric categories mapping
export const LIQUIDITY_METRICS = [
  'Current Ratio',
  'Quick Ratio',
  'Cash Ratio',
  'Working Capital Ratio',
  'Operating Cash Flow Ratio'
];

export const PROFITABILITY_METRICS = [
  'Gross Profit Margin',
  'Operating Profit Margin',
  'Net Profit Margin',
  'Return on Assets (ROA)',
  'Return on Equity (ROE)',
  'Return on Investment (ROI)',
  'EBITDA Margin',
  'Operating Ratio'
];

export const LEVERAGE_METRICS = [
  'Debt-to-Equity Ratio',
  'Debt-to-Assets Ratio',
  'Equity Multiplier',
  'Interest Coverage Ratio',
  'Debt Service Coverage Ratio',
  'Long-term Debt to Capitalization'
];

export const ANALYSIS_TYPE_LABELS: Record<AnalysisType, string> = {
  comprehensive: 'Comprehensive',
  liquidity: 'Liquidity',
  profitability: 'Profitability',
  leverage: 'Leverage',
  quick: 'Quick'
};

export const ANALYSIS_TYPE_DESCRIPTIONS: Record<AnalysisType, string> = {
  comprehensive: 'All 19 ratios + AI insights',
  liquidity: '5 liquidity ratios',
  profitability: '8 profitability ratios',
  leverage: '6 leverage ratios',
  quick: 'Fast overview with key metrics only'
};
