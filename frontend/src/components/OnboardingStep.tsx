import { useState } from 'react';
import { Button } from './ui/button';
import { Check } from 'lucide-react';

interface OnboardingStepProps {
  question: string;
  options: string[];
  multiSelect?: boolean;
  onSelect: (selected: string | string[]) => void;
  currentStep: number;
  totalSteps: number;
  onNext: () => void;
  onBack?: () => void;
}

const OnboardingStep = ({
  question,
  options,
  multiSelect = false,
  onSelect,
  currentStep,
  totalSteps,
  onNext,
  onBack,
}: OnboardingStepProps) => {
  const [selectedSingle, setSelectedSingle] = useState<string>('');
  const [selectedMultiple, setSelectedMultiple] = useState<string[]>([]);

  const handleSingleSelect = (option: string) => {
    setSelectedSingle(option);
    onSelect(option);
  };

  const handleMultipleSelect = (option: string) => {
    const newSelection = selectedMultiple.includes(option)
      ? selectedMultiple.filter((item) => item !== option)
      : [...selectedMultiple, option];
    setSelectedMultiple(newSelection);
    onSelect(newSelection);
  };

  const canProceed = multiSelect ? selectedMultiple.length > 0 : selectedSingle !== '';

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-muted-foreground code-text">
            Step {currentStep} of {totalSteps}
          </span>
          <span className="text-xs font-medium text-primary code-text">
            {Math.round((currentStep / totalSteps) * 100)}%
          </span>
        </div>
        <div className="w-full h-3 bg-card border border-border rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary to-primary/80 transition-all duration-500 rounded-full"
            style={{ width: `${(currentStep / totalSteps) * 100}%` }}
          />
        </div>
      </div>

      {/* Question */}
      <div className="bg-card/60 backdrop-blur-md border border-border rounded-2xl p-6 mb-6">
        <h2 className="text-lg font-bold text-foreground mb-2 text-center">{question}</h2>
        <p className="text-muted-foreground text-center text-xs">
          {multiSelect ? 'Select all that apply' : 'Choose one option'}
        </p>
      </div>

      {/* Options */}
      <div className="grid gap-4 mb-8">
        {options.map((option, index) => {
          const isSelected = multiSelect
            ? selectedMultiple.includes(option)
            : selectedSingle === option;

          return (
            <button
              key={option}
              onClick={() => (multiSelect ? handleMultipleSelect(option) : handleSingleSelect(option))}
              className={`group w-full p-4 text-left rounded-xl border-2 transition-all duration-300 hover:scale-[1.02] hover:-translate-y-0.5 animate-slide-up ${
                isSelected
                  ? 'border-primary bg-primary/10 shadow-lg shadow-primary/20'
                  : 'border-border bg-card/60 backdrop-blur-md hover:border-primary/50 hover:bg-card/80 hover:shadow-lg'
              } ${index === 1 ? 'animate-delay-150ms' : ''} ${index === 2 ? 'animate-delay-300ms' : ''}`}
            >
              <div className="flex items-center justify-between">
                <span className={`font-medium text-base ${isSelected ? 'text-primary' : 'text-foreground group-hover:text-primary transition-colors'}`}>
                  {option}
                </span>
                {isSelected && (
                  <div className="h-7 w-7 rounded-full bg-primary flex items-center justify-center shadow-lg">
                    <Check className="h-4 w-4 text-primary-foreground" />
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Navigation Buttons */}
      <div className="flex gap-4">
        {onBack && (
          <Button 
            variant="outline" 
            onClick={onBack} 
            className="flex-1 h-10 rounded-xl border-border hover:border-primary/50 transition-all duration-300 text-sm"
          >
            Back
          </Button>
        )}
        <Button
          onClick={onNext}
          disabled={!canProceed}
          className="flex-1 h-10 rounded-xl bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 text-primary-foreground border-0 font-medium text-sm transition-all duration-300 shadow-lg hover:shadow-primary/25 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {currentStep === totalSteps ? 'Finish & Discover' : 'Next'}
        </Button>
      </div>
    </div>
  );
};

export default OnboardingStep;
