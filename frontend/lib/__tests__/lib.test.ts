import { describe, expect, it } from "vitest";
import { buildQuery, parseErrors } from "../api";
import { roleHome } from "../format";
import { validateImage, validateLogin, validateRequiredNote, validateTicketForm } from "../validators";

const valid = { title: "Fan", description: "Loud", category: "1", building: "Block-A", floor: "", room_or_area: "" };

describe("buildQuery", () => {
  it("skips empty values and encodes the rest", () => {
    expect(buildQuery({ status: "OPEN", search: "", page: 2, x: undefined, overdue: false })).toBe("?status=OPEN&page=2");
    expect(buildQuery({})).toBe("");
    expect(buildQuery({ search: "a b" })).toBe("?search=a+b");
  });
});

describe("parseErrors", () => {
  it("uses the detail message", () => {
    expect(parseErrors({ detail: "Nope" }, 403)).toEqual({ message: "Nope", fields: {} });
  });
  it("maps field errors", () => {
    const r = parseErrors({ title: ["Required."], category: ["Bad.", "Worse."] }, 400);
    expect(r.fields).toEqual({ title: "Required.", category: "Bad. Worse." });
    expect(r.message).toMatch(/correct/i);
  });
  it("falls back to a friendly message for unknown bodies", () => {
    expect(parseErrors(null, 500).message).toMatch(/server/i);
    expect(parseErrors(null, 404).message).toMatch(/could not find/i);
  });
});

describe("validateTicketForm", () => {
  it("accepts a valid form", () => expect(validateTicketForm(valid)).toEqual({}));
  it("rejects whitespace-only and missing fields", () => {
    const e = validateTicketForm({ ...valid, title: "   ", description: "", category: "", building: " " });
    expect(Object.keys(e).sort()).toEqual(["building", "category", "description", "title"]);
  });
  it("enforces length limits", () => {
    expect(validateTicketForm({ ...valid, title: "x".repeat(201) }).title).toBeDefined();
  });
});

describe("validateImage", () => {
  const file = (type: string, size: number) => ({ type, size }) as File;
  it("allows nothing selected", () => expect(validateImage(null)).toBeNull());
  it("rejects wrong type and big files", () => {
    expect(validateImage(file("application/pdf", 10))).toMatch(/JPEG/);
    expect(validateImage(file("image/png", 6 * 1024 * 1024))).toMatch(/too large/);
    expect(validateImage(file("image/png", 1000))).toBeNull();
  });
});

describe("misc validators", () => {
  it("login", () => {
    expect(validateLogin("", "")).toEqual({ email: "Enter your email address.", password: "Enter your password." });
    expect(validateLogin("bad", "x").email).toMatch(/valid/);
    expect(validateLogin("a@b.co", "x")).toEqual({});
  });
  it("required note", () => {
    expect(validateRequiredNote("  ", "A reason")).toBe("A reason is required.");
    expect(validateRequiredNote("ok", "A reason")).toBeNull();
  });
  it("roleHome sends administrators to the manager area", () => {
    expect(roleHome("STUDENT")).toBe("/student");
    expect(roleHome("MAINTENANCE_STAFF")).toBe("/staff");
    expect(roleHome("DEPARTMENT_MANAGER")).toBe("/manager");
    expect(roleHome("ADMINISTRATOR")).toBe("/manager");
  });
});
