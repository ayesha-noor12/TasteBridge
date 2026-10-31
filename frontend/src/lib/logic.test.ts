import { describe, expect, it } from "vitest";
import { badgeFor, bannersFor, clampFamiliarity, feedbackDisabled, feedbackTarget, FEEDBACK_BUTTONS, formatCad, sliderLabel } from "./logic";
import type { Health } from "../types";

describe("source badge", () => {
  it("labels each source", () => {
    expect(badgeFor("qloo").label).toBe("Qloo-matched");
    expect(badgeFor("curated").label).toBe("Curated");
    expect(badgeFor("unverified").label).toBe("Unverified");
  });
  it("treats anything unknown as unverified", () => {
    expect(badgeFor("llm").label).toBe("Unverified");
  });
});

describe("familiarity slider", () => {
  it("clamps and rounds", () => {
    expect(clampFamiliarity(-1)).toBe(0);
    expect(clampFamiliarity(2)).toBe(1);
    expect(clampFamiliarity(0.333)).toBe(0.33);
    expect(clampFamiliarity(NaN)).toBe(0.5);
  });
  it("labels extremes and middle", () => {
    expect(sliderLabel(0)).toBe("Mostly new things");
    expect(sliderLabel(0.5)).toBe("Balanced");
    expect(sliderLabel(1)).toBe("Mostly familiar");
  });
});

describe("feedback bar", () => {
  it("has exactly the three actions", () => {
    expect(FEEDBACK_BUTTONS.map((b) => b.action)).toEqual(["too_expensive", "not_alone", "more_familiar"]);
  });
  it("sends the selected item only for too_expensive", () => {
    expect(feedbackTarget("too_expensive", "a")).toBe("a");
    expect(feedbackTarget("too_expensive", null)).toBeUndefined();
    expect(feedbackTarget("more_familiar", "a")).toBeUndefined();
  });
  it("disables buttons at their bounds", () => {
    expect(feedbackDisabled(1, "more_familiar", "small_group")).toBe(true);
    expect(feedbackDisabled(0.75, "more_familiar", "small_group")).toBe(false);
    expect(feedbackDisabled(0.5, "not_alone", "prefer_friend")).toBe(true);
  });
});

describe("formatting and banners", () => {
  it("never guesses missing cost", () => {
    expect(formatCad(null)).toBe("Cost not verified");
    expect(formatCad(12)).toBe("$12 CAD");
  });
  it("shows demo, qloo-down and llm-off banners", () => {
    const h = { qloo_mode: "mock", llm_mode: "off" } as Health;
    expect(bannersFor(h, null)).toEqual(["demo", "llm_off"]);
    expect(bannersFor({ ...h, qloo_mode: "live", llm_mode: "on" }, "qloo_unavailable")).toEqual(["qloo_down"]);
  });
});
