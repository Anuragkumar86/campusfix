import type { ReactNode } from "react";
import { RoleGuard } from "@/components/RoleGuard";

const NAV = [
  { href: "/student", label: "Dashboard" },
  { href: "/student/tickets", label: "My tickets" },
  { href: "/student/tickets/new", label: "Report an issue" },
];

export default function StudentLayout({ children }: { children: ReactNode }) {
  return <RoleGuard roles={["STUDENT"]} nav={NAV}>{children}</RoleGuard>;
}
