import { Example } from "./Example";

import styles from "./Example.module.css";

const DEFAULT_EXAMPLES: string[] = [
"What is the IOM s policy on remote work and hybrid schedules?",
"How do I apply for parental leave, and what are the entitlements?",
"What are the procedures for reporting workplace harassment or discrimination?",
"Can you explain how performance reviews work at IOM?",
"How is paid time off (PTO) calculated and tracked?",
"How do vacation policies differ between offices in different countries?",
"What are the local public holidays for employees based in Valencia?",
"Am I eligible for relocation assistance if I move to a different country office?",
"What learning and development programs are available?",
"How does internal mobility and job rotation work in this organization?",
"How do I update my emergency contact information?",
"What documents do I need to submit when requesting a leave of absence?",
"What is the code of conduct, and how is it enforced?",
"What’s the whistleblower policy, and is it anonymous?",
];

interface Props {
    onExampleClicked: (value: string) => void
}

export const ExampleList = ({ onExampleClicked }: Props) => {
    return (
        <ul className={styles.examplesNavList}>
            {DEFAULT_EXAMPLES.map((question, i) => (
                <li key={i}>
                    <Example text={question} value={question} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
