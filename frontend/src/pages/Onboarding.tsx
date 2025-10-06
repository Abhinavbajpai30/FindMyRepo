import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingStep from '@/components/OnboardingStep';
import { usePreferences, UserPreferences } from '@/contexts/PreferencesContext';

const onboardingSteps = [
  {
    question: 'What are your primary domains?',
    options: [
      'Frontend / Web',
      'Backend / APIs',
      'Mobile (iOS/Android)',
      'ML / AI / Data Science',
      'DevOps / Infrastructure',
      'Game Development',
      'Cybersecurity'
    ],
    key: 'primaryDomains',
    multiSelect: true,
  },
  {
    question: 'What best describes your role?',
    options: [
      'Student / Learner',
      'Software Developer / Engineer',
      'Tech Lead / Architect',
      'Manager / Product Owner',
      'Hobbyist / Explorer'
    ],
    key: 'role',
    multiSelect: false,
  },
  {
    question: 'What is your expertise level?',
    options: ['Beginner', 'Medium', 'Advanced'],
    key: 'expertise',
    multiSelect: false,
  },
  {
    question: 'What are your favourite languages / preferred tech stack?',
    options: [
      'JavaScript / TypeScript',
      'Python',
      'Java',
      'C# / .NET',
      'Go',
      'Rust',
      'C++',
      'PHP',
      'Ruby',
      'Swift',
      'Kotlin',
      'Dart / Flutter',
      'R',
      'Scala',
      'Clojure',
      'Haskell',
      'Elixir',
      'Julia'
    ],
    key: 'preferredLanguages',
    multiSelect: true,
  },
];

const Onboarding = () => {
  const navigate = useNavigate();
  const { setPreferences } = usePreferences();
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Partial<UserPreferences>>({});

  const handleSelect = (selected: string | string[]) => {
    const currentKey = onboardingSteps[currentStep].key as keyof UserPreferences;
    setAnswers((prev) => ({
      ...prev,
      [currentKey]: selected,
    }));
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNext = () => {
    if (currentStep < onboardingSteps.length - 1) {
      setCurrentStep((prev) => prev + 1);
      scrollToTop();
    } else {
      setPreferences(answers as UserPreferences);
      navigate('/');
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
      scrollToTop();
    }
  };

  const step = onboardingSteps[currentStep];

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Background Effects */}
      <div className="fixed inset-0 -z-10">
        {/* Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-primary/5"></div>
        
        {/* Floating Geometric Shapes */}
        <div className="absolute top-20 left-10 w-32 h-32 bg-primary/10 rounded-full blur-3xl animate-float"></div>
        <div className="absolute top-40 right-20 w-24 h-24 bg-primary/8 rounded-full blur-2xl animate-float" style={{ animationDelay: '2s' }}></div>
        <div className="absolute bottom-40 left-1/4 w-40 h-40 bg-primary/6 rounded-full blur-3xl animate-float" style={{ animationDelay: '4s' }}></div>
        
        {/* Accent Lines */}
        <div className="absolute top-32 left-0 w-32 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent animate-draw-x"></div>
        <div className="absolute top-48 right-0 w-px h-24 bg-gradient-to-b from-transparent via-primary/20 to-transparent animate-draw-y" style={{ animationDelay: '1s' }}></div>
        <div className="absolute bottom-32 left-1/3 w-24 h-px bg-gradient-to-r from-transparent via-primary/25 to-transparent animate-draw-x" style={{ animationDelay: '3s' }}></div>
      </div>

      <div className="relative z-10">
        {/* Main Content */}
        <div className="container mx-auto max-w-4xl px-4 py-12">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-foreground mb-3">
              Let's personalize your experience
            </h1>
            <p className="text-muted-foreground text-base">
              Help us understand your preferences to find the perfect repositories for you
            </p>
          </div>

          {/* Onboarding Step */}
          <OnboardingStep
            question={step.question}
            options={step.options}
            multiSelect={step.multiSelect}
            onSelect={handleSelect}
            currentStep={currentStep + 1}
            totalSteps={onboardingSteps.length}
            onNext={handleNext}
            onBack={currentStep > 0 ? handleBack : undefined}
          />
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
