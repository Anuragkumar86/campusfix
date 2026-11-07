export type IconName =
  | "home" | "list" | "plus" | "inbox" | "clock" | "chart" | "shield" | "check" | "alert"
  | "bolt" | "layers" | "search" | "logout" | "external" | "arrow-left" | "arrow-right"
  | "message" | "image" | "activity" | "menu" | "close" | "user" | "pin" | "route";

const PATHS: Record<IconName, string> = {
  home: "M3 11l9-8 9 8M5 10v10h5v-6h4v6h5V10",
  list: "M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01",
  plus: "M12 5v14M5 12h14",
  inbox: "M22 12h-6l-2 3h-4l-2-3H2M5.5 5h13L22 12v6a2 2 0 01-2 2H4a2 2 0 01-2-2v-6z",
  clock: "M12 7v5l3 2M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  chart: "M4 20V10M10 20V4M16 20v-8M22 20H2",
  shield: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z",
  check: "M5 13l4 4L19 7",
  alert: "M12 9v4m0 4h.01M10.3 3.9L2.4 17.5A2 2 0 004.1 20.5h15.8a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z",
  bolt: "M13 2L4 14h7l-1 8 9-12h-7z",
  layers: "M12 2l10 5-10 5L2 7zM2 17l10 5 10-5M2 12l10 5 10-5",
  search: "M21 21l-4.3-4.3M17 11a6 6 0 11-12 0 6 6 0 0112 0z",
  logout: "M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9",
  external: "M7 17L17 7M8 7h9v9",
  "arrow-left": "M19 12H5M12 19l-7-7 7-7",
  "arrow-right": "M5 12h14M12 5l7 7-7 7",
  message: "M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z",
  image: "M21 15l-5-5L5 21M3 5a2 2 0 012-2h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2zM8.5 10a1.5 1.5 0 100-3 1.5 1.5 0 000 3z",
  activity: "M22 12h-4l-3 9L9 3l-3 9H2",
  menu: "M4 6h16M4 12h16M4 18h16",
  close: "M6 6l12 12M18 6L6 18",
  user: "M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z",
  pin: "M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11zM12 12.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z",
  route: "M6 19a2 2 0 100-4 2 2 0 000 4zM18 9a2 2 0 100-4 2 2 0 000 4zM8 17h6a4 4 0 004-4V9",
};

export function Icon({ name, className = "h-5 w-5" }: { name: IconName; className?: string }) {
  return (
    <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d={PATHS[name]} />
    </svg>
  );
}