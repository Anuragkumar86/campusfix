"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { useAuth } from "@/lib/auth";
import type { Role } from "@/types";
import { AppShell, type NavItem } from "./AppShell";
import { Spinner } from "./Feedback";

/**
 * UX guard only: it redirects the browser. Real authorization is enforced by the
 * backend on every API call, so a user who bypasses this still gets 401/403/404.
 */
export function RoleGuard({ roles, nav, children }: { roles: Role[]; nav: NavItem[]; children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const allowed = !!user && roles.includes(user.role);

  useEffect(() => {
    if (loading) return;
    if (!user) router.replace("/login");
    else if (!allowed) router.replace("/unauthorized");
  }, [loading, user, allowed, router]);

  if (loading || !allowed) return <Spinner label="Checking your session..." />;
  return <AppShell nav={nav}>{children}</AppShell>;
}