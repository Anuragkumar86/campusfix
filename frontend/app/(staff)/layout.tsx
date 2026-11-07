import type { ReactNode } from "react";
import { RoleGuard } from "@/components/RoleGuard";

const NAV = [
  { href: "/staff", label: "Dashboard" },
  { href: "/staff/tickets", label: "Assigned tickets" },
];

export default function StaffLayout({ children }: { children: ReactNode }) {
  return <RoleGuard roles={["MAINTENANCE_STAFF"]} nav={NAV}>{children}</RoleGuard>;
}
