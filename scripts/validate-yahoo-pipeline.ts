import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { DEFAULT_YAHOO_BLOB_MAPPING_URL } from "../src/config/yahooData";
import { YAHOO_STOCK_LIST } from "../src/types/bubbleData";
import type { BubbleData } from "../src/types/bubbleData";

type Mode = "csv" | "json" | "blob";

const args = new Set(process.argv.slice(2));
const modes: Mode[] = args.size
	? (["csv", "json", "blob"].filter((mode) =>
			args.has(`--${mode}`),
		) as Mode[])
	: ["csv", "json", "blob"];

function fail(message: string): never {
	console.error(`❌ ${message}`);
	process.exit(1);
}

function assert(condition: unknown, message: string): asserts condition {
	if (!condition) fail(message);
}

function readJson(path: string): BubbleData {
	return JSON.parse(readFileSync(path, "utf8")) as BubbleData;
}

function validateBubbleData(stock: string, data: BubbleData, source: string) {
	assert(data.metadata?.stockcode === stock, `${source} metadata stock mismatch for ${stock}`);
	assert(
		Array.isArray(data.time_series_data) && data.time_series_data.length > 0,
		`${source} has no time_series_data for ${stock}`,
	);

	for (const [index, point] of data.time_series_data.entries()) {
		assert(point.date, `${source} point ${index} for ${stock} has no date`);
		assert(
			typeof point.stock_prices?.adjusted === "number",
			`${source} point ${index} for ${stock} has no adjusted price`,
		);
		assert(
			typeof point.stock_prices?.regular === "number",
			`${source} point ${index} for ${stock} has no regular price`,
		);
		assert(
			Array.isArray(point.bubble_estimates?.daily_grouped) &&
				point.bubble_estimates.daily_grouped.length >= 3,
			`${source} point ${index} for ${stock} has incomplete tau groups`,
		);
	}
}

function validateCsvArtifacts() {
	const csvDir = join(process.cwd(), "data", "csv");
	for (const stock of YAHOO_STOCK_LIST) {
		for (const suffix of ["", "_count"]) {
			const filename = `optout_${stock}${suffix}.csv`;
			const path = join(csvDir, filename);
			assert(existsSync(path), `Missing CSV artifact ${filename}`);
			const lineCount = readFileSync(path, "utf8").trim().split(/\r?\n/).length;
			assert(lineCount > 1, `CSV artifact ${filename} has no data rows`);
		}
	}
	console.log(`✅ CSV artifacts validated for ${YAHOO_STOCK_LIST.length} Yahoo tickers`);
}

function validateLocalJson() {
	const dataDir = join(process.cwd(), "public", "data");
	const files = readdirSync(dataDir).filter((filename) => filename.endsWith(".json"));
	for (const stock of YAHOO_STOCK_LIST) {
		const filename = files.find((file) =>
			file.startsWith(`bubble_data_${stock}_splitadj_`),
		);
		assert(filename, `Missing generated JSON for ${stock}`);
		const path = join(dataDir, filename);
		validateBubbleData(stock, readJson(path), filename);
	}
	console.log(`✅ Generated JSON validated for ${YAHOO_STOCK_LIST.length} Yahoo tickers`);
}

async function validateBlobMapping() {
	const envMappingUrl = process.env.VITE_YAHOO_BLOB_MAPPING_URL?.trim();
	const envBaseUrl = process.env.BLOB_BASE_URL?.trim().replace(/\/+$/, "");
	const mappingUrl =
		envMappingUrl ||
		(envBaseUrl ? `${envBaseUrl}/blob_mapping.json` : DEFAULT_YAHOO_BLOB_MAPPING_URL);

	const mappingResponse = await fetch(mappingUrl);
	assert(
		mappingResponse.ok,
		`Failed to fetch Yahoo blob mapping ${mappingUrl}: ${mappingResponse.status} ${mappingResponse.statusText}`,
	);
	const mapping = (await mappingResponse.json()) as Record<string, string>;

	for (const stock of YAHOO_STOCK_LIST) {
		const url = mapping[stock];
		assert(url, `Yahoo blob mapping is missing ${stock}`);

		const response = await fetch(url);
		assert(
			response.ok,
			`Failed to fetch mapped Yahoo JSON for ${stock}: ${response.status} ${response.statusText}`,
		);
		validateBubbleData(stock, (await response.json()) as BubbleData, url);
	}

	console.log(`✅ Live Yahoo Blob mapping validated at ${mappingUrl}`);
}

if (modes.includes("csv")) {
	validateCsvArtifacts();
}
if (modes.includes("json")) {
	validateLocalJson();
}
if (modes.includes("blob")) {
	await validateBlobMapping();
}
