// Decode EXT_meshopt_compression GLB buffers to a temporary standard GLB
// so trimesh can read HRA geometry. Execute only from the repository root.
import fs from 'node:fs';
import { MeshoptDecoder } from 'meshoptimizer';

const [inputPath, outputPath] = process.argv.slice(2);
if (!inputPath || !outputPath) throw new Error('Uso: node hra/alinhar/decoder_glb.mjs entrada.glb saida.glb (use - para stdin/stdout)');

function align4(n) { return (n + 3) & ~3; }
function chunk(type, bytes) {
  const header = Buffer.alloc(8);
  header.writeUInt32LE(bytes.length, 0);
  header.writeUInt32LE(type, 4);
  return Buffer.concat([header, bytes]);
}

const file = inputPath === '-' ? fs.readFileSync(0) : fs.readFileSync(inputPath);
if (file.toString('ascii', 0, 4) !== 'glTF' || file.readUInt32LE(4) !== 2) {
  throw new Error('Esperado GLB glTF 2.0');
}
let offset = 12;
let doc;
let bin;
while (offset < file.length) {
  const length = file.readUInt32LE(offset);
  const type = file.readUInt32LE(offset + 4);
  const bytes = file.subarray(offset + 8, offset + 8 + length);
  if (type === 0x4e4f534a) doc = JSON.parse(bytes.toString('utf8').trim());
  if (type === 0x004e4942) bin = bytes;
  offset += 8 + length;
}
if (!doc || !bin) throw new Error('GLB sem JSON ou BIN chunk');
await MeshoptDecoder.ready;

const decoded = [];
let cursor = 0;
for (const view of doc.bufferViews ?? []) {
  const ext = view.extensions?.EXT_meshopt_compression;
  let bytes;
  if (ext) {
    const sourceBuffer = ext.buffer === 0 ? bin : null;
    if (!sourceBuffer) throw new Error(`Buffer meshopt ausente: ${ext.buffer}`);
    const src = sourceBuffer.subarray(ext.byteOffset ?? 0, (ext.byteOffset ?? 0) + ext.byteLength);
    bytes = new Uint8Array(ext.count * ext.byteStride);
    MeshoptDecoder.decodeGltfBuffer(bytes, ext.count, ext.byteStride, src,
      ext.mode, ext.filter);
    delete view.extensions.EXT_meshopt_compression;
    if (Object.keys(view.extensions).length === 0) delete view.extensions;
  } else {
    const sourceBuffer = view.buffer === 0 ? bin : null;
    if (!sourceBuffer) throw new Error(`Buffer view sem meshopt e sem buffer ${view.buffer}`);
    const start = view.byteOffset ?? 0;
    bytes = sourceBuffer.subarray(start, start + view.byteLength);
  }
  cursor = align4(cursor);
  view.buffer = 0;
  view.byteOffset = cursor;
  view.byteLength = bytes.length;
  decoded.push({ offset: cursor, bytes: Buffer.from(bytes) });
  cursor += bytes.length;
}

const outputBin = Buffer.alloc(align4(cursor));
for (const part of decoded) part.bytes.copy(outputBin, part.offset);
doc.buffers = [{ byteLength: cursor }];
if (doc.extensionsUsed) doc.extensionsUsed = doc.extensionsUsed.filter(x => x !== 'EXT_meshopt_compression');
if (doc.extensionsRequired) doc.extensionsRequired = doc.extensionsRequired.filter(x => x !== 'EXT_meshopt_compression');
const jsonBytes = Buffer.from(JSON.stringify(doc), 'utf8');
const paddedJson = Buffer.alloc(align4(jsonBytes.length), 0x20);
jsonBytes.copy(paddedJson);
const output = Buffer.concat([
  Buffer.from('glTF'), Buffer.from([2, 0, 0, 0]), Buffer.alloc(4),
  chunk(0x4e4f534a, paddedJson), chunk(0x004e4942, outputBin),
]);
output.writeUInt32LE(output.length, 8);
if (outputPath === '-') fs.writeFileSync(1, output);
else fs.writeFileSync(outputPath, output);
if (outputPath !== '-') console.log(`decoded ${doc.meshes?.length ?? 0} meshes; ${cursor} bytes`);
