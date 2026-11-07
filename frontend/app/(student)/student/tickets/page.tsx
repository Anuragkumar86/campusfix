import Link from "next/link";
import { PageHeader } from "@/components/Feedback";
import { TicketList } from "@/components/TicketList";

export default function Page() {
  return (
    <div>
      <PageHeader title="My tickets" subtitle="Every issue you have reported." actions={<Link href="/student/tickets/new" className="btn-primary">Report an issue</Link>} />
      <TicketList basePath="/student/tickets" showAssignee={false} emptyTitle="You have not reported any issues yet" emptyHint="Use “Report an issue” to create your first ticket." />
    </div>
  );
}
