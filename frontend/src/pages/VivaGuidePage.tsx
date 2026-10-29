import React, { useState } from 'react';
import { 
  GraduationCap, 
  HelpCircle, 
  CheckCircle2, 
  ChevronDown, 
  ChevronUp, 
  Search, 
  Sparkles,
  BookOpen
} from 'lucide-react';

interface QuestionItem {
  id: number;
  category: string;
  question: string;
  answer: string;
  examinerTip: string;
}

const QUESTIONS: QuestionItem[] = [
  {
    id: 1,
    category: 'Problem Statement & Motivation',
    question: 'What is the official problem statement addressed by DBGuard?',
    answer: 'The project addresses a production dilemma where a compressed database export experienced a 30% row increase compared to an earlier export, but its compressed file size decreased by 20%. Management suspected corruption. Because the table is massive, restoring it into a secondary scratch database was operationally impossible due to tablespace and time constraints. DBGuard verifies integrity without full restoration.',
    examinerTip: 'Emphasize that decompressing into RAM or disk is disallowed due to OOM/disk limits.'
  },
  {
    id: 2,
    category: 'Problem Statement & Motivation',
    question: 'Why can we not simply restore the database into a temporary database to verify it?',
    answer: 'In production enterprise systems with multi-hundred-gigabyte or terabyte tables, provisioning equivalent IOPS and scratch storage is financially prohibitive and takes dozens of hours. Furthermore, restoring writes to disk, creating heavy operational disruption.',
    examinerTip: 'Use terms like "IOPS bottleneck", "tablespace exhaustion", and "recovery time objective (RTO)".'
  },
  {
    id: 3,
    category: 'Problem Statement & Motivation',
    question: 'Does a smaller compressed file automatically mean the export is corrupted or incomplete?',
    answer: 'No. Compression algorithms like DEFLATE and LZMA compress data based on repetition and information entropy. If new rows contain repeated values, shorter text fields, or high NULL ratios, the compressed file can be substantially smaller despite containing more records.',
    examinerTip: 'Mention Shannon entropy: lower entropy = higher compression ratio.'
  },
  {
    id: 4,
    category: 'Problem Statement & Motivation',
    question: 'What are the three distinct integrity layers in DBGuard?',
    answer: '1. Physical Container Integrity (container headers, block bitstream, CRC-32 trailer). 2. Logical Structure Integrity (delimiters, UTF-8 validity, column count, schema fingerprint). 3. Provenance & Completeness (reconciling with independent database export manifests).',
    examinerTip: 'Examiners love when you distinguish physical stream validity from logical completeness.'
  },
  {
    id: 5,
    category: 'Problem Statement & Motivation',
    question: 'Can computing a SHA-256 hash on an export file prove it contains all source rows?',
    answer: 'No. A hash computed after the export only proves that the file has not mutated since the hash was generated. If rows were missed during the SQL query or network transmission before hashing, the hash will still match a truncated file. You must have an independent manifest from the database engine.',
    examinerTip: 'Distinguish between post-hoc observation and export-pipeline provenance.'
  },
  {
    id: 6,
    category: 'Compression & Entropy',
    question: 'Explain how the DEFLATE compression algorithm works.',
    answer: 'DEFLATE combines LZ77 (Lempel-Ziv dictionary-based deduplication) with Huffman entropy coding. LZ77 replaces repeated occurrences of data with references to previous identical sequences (length-distance pairs). Huffman coding encodes frequent symbols using shorter bit-lengths.',
    examinerTip: 'Reference gzip RFC 1951 and RFC 1952.'
  },
  {
    id: 7,
    category: 'Compression & Entropy',
    question: 'How does DBGuard detect gzip stream truncation?',
    answer: 'Standard gzip contains a 4-byte CRC-32 and a 4-byte ISIZE (modulo 2^32 uncompressed byte count) in its 8-byte trailer. DBGuard reads until the container EOF, validates the CRC-32 against the running stream, and verifies the trailer ISIZE.',
    examinerTip: 'If gzip terminates unexpectedly without the trailer, zlib/gzip raises an EOFError or truncated block error.'
  },
  {
    id: 8,
    category: 'Compression & Entropy',
    question: 'What is a compression bomb (zip bomb) and how does DBGuard protect against it?',
    answer: 'A zip bomb is a tiny compressed file that expands into petabytes of repeated zeroes, exhausting RAM or disk. DBGuard prevents this by checking the expansion ratio dynamically and enforcing maximum decompressed byte thresholds.',
    examinerTip: 'State that DBGuard enforces a safety ceiling (e.g., maximum ratio of 1000:1).'
  },
  {
    id: 9,
    category: 'Compression & Entropy',
    question: 'What compression containers are supported in DBGuard?',
    answer: 'Gzip (.gz), Bzip2 (.bz2), and XZ / LZMA (.xz), as well as uncompressed raw CSV and SQL dump streams.',
    examinerTip: 'Mention that all three are decompressed using bounded chunk generators.'
  },
  {
    id: 10,
    category: 'Compression & Entropy',
    question: 'What is the bytes-per-record metric and why is it useful?',
    answer: 'Bytes-per-record is calculated as (Total Decompressed Bytes / Total Rows). If row counts increase by 30% but bytes-per-record drops sharply, it confirms that newly inserted records are significantly shorter or contain less entropy.',
    examinerTip: 'In our test case, bytes-per-row dropped from 85.2 to 52.8 bytes.'
  },
  {
    id: 11,
    category: 'Streaming Architecture & Memory',
    question: 'What is bounded-memory streaming and what is DBGuard’s space complexity?',
    answer: 'DBGuard operates in O(B) space complexity, where B is the fixed buffer chunk size (64 KB). It does not load the entire compressed file or the entire decompressed dataset into RAM. Peak resident RAM stays under 2 MB regardless of whether the archive is 10 MB or 100 GB.',
    examinerTip: 'Contrast O(B) with O(N) where N is the total uncompressed file size.'
  },
  {
    id: 12,
    category: 'Streaming Architecture & Memory',
    question: 'How does DBGuard parse CSV lines without materializing the whole file?',
    answer: 'DBGuard creates a custom RawIOBase stream reader adapter around a Python generator of decompressed 64 KB chunks. The csv module or io.TextIOWrapper reads incrementally from this adapter, emitting one record at a time.',
    examinerTip: 'Highlight the ChunkGeneratorReader class in dbguard/stream/reader.py.'
  },
  {
    id: 13,
    category: 'Streaming Architecture & Memory',
    question: 'How does single-pass stream tapping work in DBGuard?',
    answer: 'As uncompressed chunks flow from the decompressor, a stream tapper simultaneously updates: 1) the running decompressed SHA-256 digest, 2) the chunk Merkle tree leaf hashes (every 1 MB), 3) the CSV/SQL record parser, and 4) column statistics. All in a single pass.',
    examinerTip: 'Single-pass avoids multiple I/O passes over slow disk or network storage.'
  },
  {
    id: 14,
    category: 'Streaming Architecture & Memory',
    question: 'What happens if a record contains a malformed line or mismatched column count?',
    answer: 'DBGuard increments a malformed_rows counter, records the byte offset, stores the error sample, and flags a structural integrity anomaly while continuing to process the remaining rows to determine recoverable records.',
    examinerTip: 'This enables the RECOVERY_POSSIBLE_WITH_ERRORS classification.'
  },
  {
    id: 15,
    category: 'Streaming Architecture & Memory',
    question: 'What is the time complexity of DBGuard’s verification engine?',
    answer: 'The time complexity is O(N) where N is the total byte size of the export, because decompression, SHA-256 hashing, and delimited record parsing all run in linear time with a single pass.',
    examinerTip: 'Point out benchmark results showing constant throughput of ~150,000+ rec/s.'
  },
  {
    id: 16,
    category: 'Cryptographic Hashing & Merkle Trees',
    question: 'Why does DBGuard use Chunk Hashes and a Merkle Tree in addition to a whole-file SHA-256?',
    answer: 'A whole-file hash can only detect that corruption exists somewhere in the file. A Merkle tree hashes 1 MB chunks independently, enabling exact pinpointing of which specific chunk failed, facilitating partial data salvage.',
    examinerTip: 'Mention that Merkle root verification allows O(log M) chunk verification.'
  },
  {
    id: 17,
    category: 'Cryptographic Hashing & Merkle Trees',
    question: 'What is a Schema Fingerprint in DBGuard?',
    answer: 'A schema fingerprint is a SHA-256 digest of the canonical column names and inferred types: SHA-256(col1:type1|col2:type2|...). If a column is dropped or reordered between exports, the schema fingerprint immediately mismatches.',
    examinerTip: 'Show that this catches schema drift between production backups.'
  },
  {
    id: 18,
    category: 'Cryptographic Hashing & Merkle Trees',
    question: 'What is HMAC authentication in DBGuard manifests?',
    answer: 'HMAC-SHA256 generates a keyed cryptographic signature over the manifest contents. This prevents an attacker or corrupted script from tampering with both the export and the manifest simultaneously.',
    examinerTip: 'Highlight that HMAC requires a shared secret between export script and verifier.'
  },
  {
    id: 19,
    category: 'Cryptographic Hashing & Merkle Trees',
    question: 'What information is stored in a DBGuard Schema 1.0 Manifest?',
    answer: 'Provenance type (TRUSTED vs OBSERVATIONAL), export timestamp, database host/table name, expected row count, compressed byte size, uncompressed byte size, compressed SHA-256, decompressed SHA-256, chunk Merkle root, and schema fingerprint.',
    examinerTip: 'Reference dbguard/manifest/schema.py.'
  },
  {
    id: 20,
    category: 'Cryptographic Hashing & Merkle Trees',
    question: 'What is the difference between CRC32 and SHA-256 in DBGuard?',
    answer: 'CRC32 is an error-detecting cyclic redundancy code built into container headers to detect accidental transmission errors or disk bitflips. SHA-256 is a 256-bit cryptographic hash function designed to resist intentional tampering and collisions.',
    examinerTip: 'Mention that gzip uses CRC-32 while DBGuard computes SHA-256 on top.'
  },
  {
    id: 21,
    category: 'Full-Stack Architecture',
    question: 'Describe the full-stack architecture of DBGuard.',
    answer: 'The system uses a React + TypeScript + Vite frontend with Tailwind CSS and Recharts for interactive visualization. The backend is built with FastAPI (Python 3.12) with asynchronous streaming endpoints and an SQLite database via SQLAlchemy for audit logs and benchmarks.',
    examinerTip: 'Emphasize clean separation: REST API backend + reactive UI.'
  },
  {
    id: 22,
    category: 'Full-Stack Architecture',
    question: 'How are file uploads handled without buffering giant files in FastAPI memory?',
    answer: 'FastAPI uses Starlette’s UploadFile, which spools incoming files exceeding 1 MB directly to a temporary file on disk. The streaming engine then opens that file stream in 64 KB buffers, ensuring backend server RAM never spikes.',
    examinerTip: 'Explain that UploadFile avoids reading file.read() all at once into RAM.'
  },
  {
    id: 23,
    category: 'Full-Stack Architecture',
    question: 'How does the comparator route (/api/comparisons) evaluate two files?',
    answer: 'It streams both files through the engine, calculates delta percentages for row counts, compressed sizes, and decompressed sizes, checks schema compatibility, and executes anomaly rules (such as negative size divergence).',
    examinerTip: 'This route powers the paradox demonstration.'
  },
  {
    id: 24,
    category: 'Full-Stack Architecture',
    question: 'What export report formats are generated by DBGuard?',
    answer: '1. Executive PDF report (built with ReportLab, featuring status tables and DBA recommendations). 2. Cryptographic JSON manifest. 3. Tabular CSV summary of metrics and anomalies.',
    examinerTip: 'Mention ReportLab in Python for dynamic vector PDF generation.'
  },
  {
    id: 25,
    category: 'Full-Stack Architecture',
    question: 'What are the 6 recovery classifications in DBGuard?',
    answer: '1. VERIFIED_WITHIN_SCOPE (all clean with manifest). 2. LIKELY_USABLE_BUT_NOT_FULLY_VERIFIED (clean, but no manifest). 3. RECOVERY_POSSIBLE_WITH_ERRORS (truncated tail, salvageable). 4. INTEGRITY_FAILURE (bad CRC, corrupt stream). 5. INCONCLUSIVE (ambiguous anomaly). 6. UNSUPPORTED_FORMAT.',
    examinerTip: 'Memorize these 6 classifications for external viva examination.'
  }
];

export const VivaGuidePage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedIds, setExpandedIds] = useState<number[]>([1, 3, 11]);

  const categories = ['ALL', ...Array.from(new Set(QUESTIONS.map((q) => q.category)))];

  const toggleExpand = (id: number) => {
    setExpandedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const expandAll = () => setExpandedIds(QUESTIONS.map((q) => q.id));
  const collapseAll = () => setExpandedIds([]);

  const filteredQuestions = QUESTIONS.filter((q) => {
    const matchesCategory = selectedCategory === 'ALL' || q.category === selectedCategory;
    const matchesSearch =
      q.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      q.answer.toLowerCase().includes(searchQuery.toLowerCase()) ||
      q.examinerTip.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Title */}
      <div className="border-b border-slate-800 pb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <GraduationCap className="w-8 h-8 text-cyan-400" />
          <span>Interactive Viva & Oral Exam Guide</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          25 comprehensive questions, examiner tips, and academic proofs prepared for university external project evaluation.
        </p>
      </div>

      {/* Hero Banner */}
      <div className="p-6 rounded-2xl border border-cyan-800/60 bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <span className="text-xs uppercase font-mono tracking-wider font-semibold text-cyan-400">
            External Viva Master Cheat-Sheet
          </span>
          <h2 className="text-xl font-bold text-white">Mastering the Viva Defense</h2>
          <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
            The key to scoring highest marks is emphasizing that <strong className="text-white">a 30% row increase with 20% size reduction is an explainable entropy phenomenon</strong>, and proving that DBGuard validates integrity in <strong className="text-cyan-300 font-mono">O(B) memory</strong> without requiring secondary tablespaces.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={expandAll}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
          >
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
          >
            Collapse All
          </button>
        </div>
      </div>

      {/* Search and Category Filters */}
      <div className="space-y-4">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search viva questions, examiner tips, concepts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900/60 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500 transition-colors"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${
                selectedCategory === cat
                  ? 'bg-cyan-500 text-slate-950 font-semibold shadow-md shadow-cyan-500/20'
                  : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Accordion List */}
      <div className="space-y-3">
        {filteredQuestions.map((q) => {
          const isExpanded = expandedIds.includes(q.id);
          return (
            <div
              key={q.id}
              className={`rounded-2xl border transition-all ${
                isExpanded
                  ? 'border-cyan-800/80 bg-slate-900/80'
                  : 'border-slate-800/80 bg-slate-900/40 hover:border-slate-700'
              }`}
            >
              <button
                onClick={() => toggleExpand(q.id)}
                className="w-full p-4 text-left flex items-start justify-between gap-4"
              >
                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 text-xs font-mono font-bold flex items-center justify-center mt-0.5">
                    {q.id}
                  </span>
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold block mb-1">
                      {q.category}
                    </span>
                    <h3 className="text-sm font-semibold text-white">{q.question}</h3>
                  </div>
                </div>
                <div className="p-1 rounded-lg bg-slate-800 text-slate-400 flex-shrink-0">
                  {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </div>
              </button>

              {isExpanded && (
                <div className="px-5 pb-5 pt-1 space-y-3 border-t border-slate-800/60 mt-1">
                  <p className="text-xs text-slate-300 leading-relaxed font-sans">{q.answer}</p>
                  <div className="p-3 rounded-xl bg-slate-950 border border-cyan-900/40 flex items-start gap-2.5">
                    <Sparkles className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="text-[11px] font-semibold text-cyan-300 block">
                        Examiner Viva Tip
                      </span>
                      <span className="text-[11px] text-slate-400 leading-relaxed">
                        {q.examinerTip}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
