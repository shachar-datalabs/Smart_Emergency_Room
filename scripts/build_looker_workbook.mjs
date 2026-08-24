import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const source = JSON.parse(await fs.readFile(path.join(ROOT, "data", "looker_workbook_source.json"), "utf8"));
const outputDir = path.join(ROOT, "exports", "looker");
const previewDir = path.join(outputDir, "previews");
await fs.mkdir(previewDir, { recursive: true });

const workbook = Workbook.create();
const excelUtcSerial = (value) => Date.parse(value) / 86400000 + 25569;
const columnName = (index) => {
  let name = "";
  for (let value = index + 1; value > 0; value = Math.floor((value - 1) / 26)) {
    name = String.fromCharCode(65 + ((value - 1) % 26)) + name;
  }
  return name;
};
const dateFields = new Set(["snapshot_time", "window_start", "window_end", "arrival_time", "last_event_time", "last_update_timestamp", "generated_at"]);
const percentFields = new Set(["admission_rate"]);
const integerFields = new Set(["active_patients", "arrivals", "admissions", "discharges", "patients_above_expected", "high_attention_patients", "critical_attention_patients", "new_arrivals", "high_attention_count", "triage_level", "age", "heart_rate", "systolic_bp", "diastolic_bp", "spo2", "attention_score", "patient_count", "record_count", "arrival_hour"]);

for (const sheetName of source.sheet_order) {
  const rows = source.tables[sheetName];
  const headers = source.columns[sheetName];
  const values = [headers, ...rows.map((row) => headers.map((header) => {
    const value = row[header];
    if (value === null || value === undefined) return null;
    if (dateFields.has(header)) return excelUtcSerial(value);
    return value;
  }))];
  const sheet = workbook.worksheets.add(sheetName);
  sheet.showGridLines = false;
  sheet.getRangeByIndexes(0, 0, values.length, headers.length).values = values;
  sheet.freezePanes.freezeRows(1);
  const header = sheet.getRangeByIndexes(0, 0, 1, headers.length);
  header.format = {
    fill: "#17233C",
    font: { bold: true, color: "#FFFFFF" },
    rowHeight: 30,
    verticalAlignment: "center",
  };
  const used = sheet.getRangeByIndexes(0, 0, values.length, headers.length);
  used.format.font = { name: "Arial", size: 10 };
  used.format.borders = { insideHorizontal: { style: "thin", color: "#E5E9F2" } };
  used.format.autofitColumns();
  for (let index = 0; index < headers.length; index += 1) {
    const column = sheet.getRangeByIndexes(1, index, rows.length, 1);
    if (dateFields.has(headers[index])) column.format.numberFormat = "yyyy-mm-dd hh:mm:ss";
    if (percentFields.has(headers[index])) column.format.numberFormat = "0.0%";
    if (integerFields.has(headers[index])) column.format.numberFormat = "#,##0";
    const width = ["attention_reason", "description", "historical_cohort", "cohort_key", "check_name"].includes(headers[index])
      ? 58
      : Math.min(32, Math.max(16, headers[index].length + 3));
    sheet.getRangeByIndexes(0, index, values.length, 1).format.columnWidth = width;
  }
  const tableName = `${sheetName.replaceAll("_", "")}Table`;
  const table = sheet.tables.add(used, true, tableName);
  table.showBandedColumns = false;
  table.showFilterButton = true;
  if (sheetName === "ACTIVE_PATIENTS") {
    const attentionColumn = headers.indexOf("attention_level");
    const range = sheet.getRangeByIndexes(1, attentionColumn, rows.length, 1);
    range.conditionalFormats.add("containsText", { text: "CRITICAL", format: { fill: "#B91C1C", font: { bold: true, color: "#FFFFFF" } } });
    range.conditionalFormats.add("containsText", { text: "HIGH", format: { fill: "#F97316", font: { bold: true, color: "#FFFFFF" } } });
    range.conditionalFormats.add("containsText", { text: "MEDIUM", format: { fill: "#FDE68A", font: { color: "#78350F" } } });
  }
}

for (const sheetName of source.sheet_order) {
  const lastColumn = columnName(source.columns[sheetName].length - 1);
  const lastRow = Math.min(source.tables[sheetName].length + 1, 25);
  const preview = await workbook.render({ sheetName, range: `A1:${lastColumn}${lastRow}`, scale: 1, format: "png" });
  await fs.writeFile(path.join(previewDir, `${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
const workbookPath = path.join(outputDir, "Smart_Emergency_Room_Looker_Source.xlsx");
await output.save(workbookPath);
const reopened = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const names = reopened.worksheets.items.map((sheet) => sheet.name);
if (JSON.stringify(names) !== JSON.stringify(source.sheet_order)) {
  throw new Error(`Workbook sheet mismatch: ${JSON.stringify(names)}`);
}
console.log(`Workbook created with ${source.sheet_order.length} sheets.`);
process.exit(0);
