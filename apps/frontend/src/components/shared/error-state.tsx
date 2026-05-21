import { NoticeBanner } from "./notice-banner";
import { buttonToneStyles, sharedButtonBase } from "./ui-styles";

export const ErrorState = ({
  message = "Something went wrong",
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) => {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12 text-center" role="alert">
      <NoticeBanner
        tone="danger"
        title={message}
        description="Please retry or go back and try again."
        className="w-full max-w-md text-left"
      />
      {onRetry && (
        <button
          onClick={onRetry}
          className={`${sharedButtonBase} ${buttonToneStyles.primary}`}
        >
          Try again
        </button>
      )}
    </div>
  );
}
