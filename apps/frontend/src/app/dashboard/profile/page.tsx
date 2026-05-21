import { Suspense } from "react";
import { ProfilePage as ProfilePageContent } from "@/components/profile/profile-page";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { UI_LABELS } from "@/lib/constants";

const ProfilePage = () => {
  return (
    <Suspense fallback={<LoadingSpinner text={UI_LABELS.loading} />}>
      <ProfilePageContent />
    </Suspense>
  );
}
export default ProfilePage;
