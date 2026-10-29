import {
  AnalysisDetail,
  AnalysisSummary,
  BenchmarkItem,
  ComparisonSummary,
  DemoScenario
} from '../types';

const API_BASE = '/api';

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  async getFormats() {
    const res = await fetch(`${API_BASE}/formats`);
    if (!res.ok) throw new Error('Failed to fetch format capabilities');
    return res.json();
  },

  async uploadAnalysis(
    file: File,
    manifestFile?: File | null,
    dataFormat?: string,
    secretKey?: string
  ): Promise<AnalysisDetail> {
    const formData = new FormData();
    formData.append('file', file);
    if (manifestFile) formData.append('manifest_file', manifestFile);
    if (dataFormat) formData.append('data_format', dataFormat);
    if (secretKey) formData.append('secret_key', secretKey);

    const res = await fetch(`${API_BASE}/analyses`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Analysis failed' }));
      throw new Error(err.detail || 'Analysis request failed');
    }
    return res.json();
  },

  async listAnalyses(): Promise<AnalysisSummary[]> {
    const res = await fetch(`${API_BASE}/analyses`);
    if (!res.ok) throw new Error('Failed to fetch analysis history');
    return res.json();
  },

  async getAnalysisDetail(analysisId: string): Promise<AnalysisDetail> {
    const res = await fetch(`${API_BASE}/analyses/${analysisId}`);
    if (!res.ok) throw new Error('Failed to load analysis details');
    return res.json();
  },

  async deleteAnalysis(analysisId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/analyses/${analysisId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete analysis');
  },

  async compareExports(oldFile: File, newFile: File): Promise<ComparisonSummary> {
    const formData = new FormData();
    formData.append('old_file', oldFile);
    formData.append('new_file', newFile);

    const res = await fetch(`${API_BASE}/comparisons`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Comparison failed' }));
      throw new Error(err.detail || 'Comparison request failed');
    }
    return res.json();
  },

  async validateManifest(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/manifests/validate`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Manifest validation failed' }));
      throw new Error(err.detail || 'Validation failed');
    }
    return res.json();
  },

  async generateManifest(file: File, sourceId: string, isTrusted: boolean, secretKey?: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_identifier', sourceId);
    formData.append('is_trusted', String(isTrusted));
    if (secretKey) formData.append('secret_key', secretKey);

    const res = await fetch(`${API_BASE}/manifests/generate`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Manifest generation failed' }));
      throw new Error(err.detail || 'Generation failed');
    }
    return res.json();
  },

  async getBenchmarks(): Promise<BenchmarkItem[]> {
    const res = await fetch(`${API_BASE}/benchmarks`);
    if (!res.ok) throw new Error('Failed to load benchmarks');
    return res.json();
  },

  async runLiveBenchmark(rows: number, repetitive: boolean) {
    const res = await fetch(`${API_BASE}/benchmarks/run?rows=${rows}&repetitive=${repetitive}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Benchmark execution failed');
    return res.json();
  },

  async getDemoScenarios(): Promise<DemoScenario[]> {
    const res = await fetch(`${API_BASE}/demo/scenarios`);
    if (!res.ok) throw new Error('Failed to fetch demo scenarios');
    return res.json();
  },

  async runDemoScenario(scenarioId: string): Promise<AnalysisDetail> {
    const res = await fetch(`${API_BASE}/demo/run/${scenarioId}`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to run scenario' }));
      throw new Error(err.detail || 'Scenario execution failed');
    }
    return res.json();
  },

  getReportDownloadUrl(analysisId: string, format: 'pdf' | 'json' | 'csv'): string {
    return `${API_BASE}/analyses/${analysisId}/report?format=${format}`;
  }
};

