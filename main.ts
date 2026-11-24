/**
 * main.ts — make.fun 'Charm the Cartographers' entry helper.
 *
 * Reads entry.png from the directory this file lives in (import.meta.url),
 * writes a byte-identical copy to /output/entry.png, then validates:
 *   - the file exists
 *   - it is a PNG (magic bytes)
 *   - it is at most 1 MiB (1_048_576 bytes)
 *
 * Exits 0 on success, non-zero with a clear message on any failure.
 */
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC = join(HERE, "entry.png");
const OUT_DIR = "/output";
const OUT = join(OUT_DIR, "entry.png");
const MAX_BYTES = 1_048_576;
const PNG_MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function fail(msg: string): never {
  console.error(`[main] FAIL: ${msg}`);
  process.exit(1);
}

function main(): void {
  const data = readFileSync(SRC); // throws with a clear ENOENT message if missing
  if (data.length > MAX_BYTES) {
    fail(`entry.png is ${data.length} bytes; limit is ${MAX_BYTES}`);
  }
  if (data.length < 8 || !data.subarray(0, 8).equals(PNG_MAGIC)) {
    fail("entry.png is not a PNG (bad magic bytes)");
  }
  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(OUT, data);
  const st = statSync(OUT);
  if (!st.isFile()) {
    fail("output path is not a regular file");
  }
  const written = readFileSync(OUT);
  if (written.length !== data.length || !written.equals(data)) {
    fail("output file is not byte-identical to entry.png");
  }
  const sha = createHash("sha256").update(data).digest("hex");
  console.log(`[main] OK: ${st.size} bytes written to ${OUT}`);
  console.log(`[main] OK: sha256 ${sha}`);
}

try {
  main();
} catch (err) {
  fail(err instanceof Error ? err.message : String(err));
}