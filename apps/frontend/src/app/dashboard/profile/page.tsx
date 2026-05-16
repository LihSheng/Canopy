import { Suspense } from "react";
import { ProfilePage as ProfilePageContent } from "@/components/profile-v2/profile-page";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

export default function ProfilePage() {
  return (
    <Suspense fallback={<LoadingSpinner text="Loading profile..." />}>
      <ProfilePageContent />
    </Suspense>
  );
}
