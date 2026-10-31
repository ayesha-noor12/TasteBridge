import type { Profile } from "../types";

export interface Persona {
  name: string; // invented first name, not a real person
  blurb: string;
  img: string;
  profile: Profile;
}

const base = { destination_city: "Toronto", comfort: "small_group" as const, familiarity: 0.5 };

/** Invented example students. They are inputs only: every result comes from the live pipeline. */
export const PERSONAS: Persona[] = [
  {
    name: "Ayesha",
    blurb: "Misses Coke Studio sessions and long chai evenings.",
    img: "/img/music.svg",
    profile: {
      ...base,
      diet: ["none"],
      origin: "Pakistan",
      preserve: ["music", "food", "friends"],
      loved_items: [
        { text: "Coke Studio", type: "artist" },
        { text: "Biryani", type: "dish" },
        { text: "chai with friends", type: "activity" },
      ],
      budget_per_activity_cad: 20,
      hours_per_week: 10,
      max_travel_minutes: 40,
    },
  },
  {
    name: "Tobi",
    blurb: "Lives for Afrobeats and a proper pot of jollof.",
    img: "/img/food.svg",
    profile: {
      ...base,
      diet: ["none"],
      origin: "Nigeria",
      preserve: ["music", "food", "nightlife"],
      loved_items: [
        { text: "Burna Boy", type: "artist" },
        { text: "Wizkid", type: "artist" },
        { text: "Jollof rice", type: "dish" },
      ],
      budget_per_activity_cad: 15,
      hours_per_week: 8,
      max_travel_minutes: 45,
    },
  },
  {
    name: "Minji",
    blurb: "K-drama nights and late street-food runs.",
    img: "/img/social.svg",
    profile: {
      ...base,
      diet: ["none"],
      origin: "South Korea",
      preserve: ["food", "familiarity", "friends"],
      loved_items: [
        { text: "Crash Landing on You", type: "show" },
        { text: "Tteokbokki", type: "dish" },
        { text: "IU", type: "artist" },
      ],
      budget_per_activity_cad: 25,
      hours_per_week: 12,
      max_travel_minutes: 30,
    },
  },
];
