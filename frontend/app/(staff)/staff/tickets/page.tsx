import { PageHeader } from "@/components/Feedback";
import { TicketList } from "@/components/TicketList";

export default function Page() {
  return (
    <div>
      <PageHeader title="Assigned tickets" subtitle="Tickets currently assigned to you." />
      <TicketList basePath="/staff/tickets" showReporter showAssignee={false} emptyTitle="No tickets are assigned to you" emptyHint="New assignments from your manager will appear here." />
    </div>
  );
}
