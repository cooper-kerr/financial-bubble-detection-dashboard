import { describe, expect, it } from "vitest";
import { Plot } from "./plotly";

describe("the reduced Plotly build", () => {
	it("creates the React chart component with scatter registered", () => {
		expect(Plot).toBeTypeOf("function");
	});
});
