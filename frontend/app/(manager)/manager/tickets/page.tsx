import { PageHeader } from "@/components/Feedback";
import { TicketList } from "@/components/TicketList";

export default async function Page({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const q = await searchParams;
  return (
    <div>
      <PageHeader title="Ticket queue" subtitle="Tickets in your scope. Open one to set priority or assign staff." />
      <TicketList
        key={JSON.stringify(q)}
        basePath="/manager/tickets"
        showReporter
        initial={{ unassigned: q.unassigned === "true", overdue: q.overdue === "true", status: q.status ?? "" }}
        emptyTitle="No tickets in your department yet"
        emptyHint="New tickets will appear here as soon as students report them."
      />
    </div>
  );
}
