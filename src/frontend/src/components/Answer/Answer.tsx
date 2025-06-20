import { useMemo, useState } from "react";
import { Stack, IconButton } from "@fluentui/react";
import DOMPurify from "dompurify";

import styles from "./Answer.module.css";

import { RAGChatCompletion } from "../../api/models";
import { parseAnswerToHtml } from "./AnswerParser";
import { AnswerIcon } from "./AnswerIcon";

interface Props {
    answer: RAGChatCompletion;
    isSelected?: boolean;
    isStreaming: boolean;
    onCitationClicked: (filePath: string) => void;
    onThoughtProcessClicked: () => void;
    onSupportingContentClicked: () => void;
    onFollowupQuestionClicked?: (question: string) => void;
    showFollowupQuestions?: boolean;
}



export const Answer = ({
    answer,
    isSelected,
    isStreaming,
    onCitationClicked,
    onThoughtProcessClicked,
    onSupportingContentClicked,
    onFollowupQuestionClicked,
    showFollowupQuestions
}: Props) => {
    const [isReferencesCollapsed, setIsReferencesCollapsed] = useState(true);
    const followupQuestions = answer.context.followup_questions;
    const messageContent = answer.message.content;
    const parsedAnswer = useMemo(() => parseAnswerToHtml(messageContent, isStreaming, onCitationClicked), [answer]);

    const sanitizedAnswerHtml = DOMPurify.sanitize(parsedAnswer.answerHtml);


    const ImpactSummary = ({ question, impacts }: { question: string; impacts: any }) => {
        if (!impacts?.energy?.value || !impacts?.gwp?.value) return null;

        return (
            <div style={{ fontSize: "0.85rem", color: "#555", padding: "4px 12px" }}>
                ⚡ Energy used: {impacts.energy.value.toFixed(4)} kWh
                (~{(impacts.energy.value / 0.06).toFixed(0)} mins of LED bulb usage)<br />
                🌍 CO₂ emitted: {impacts.gwp.value.toFixed(4)} kg
                (~{(impacts.gwp.value / 0.21 * 1000).toFixed(0)} m driven in a petrol car)<br />
                📧 <a
                    href={`mailto:elegoupil@iom.int?subject=Chat Feedback&body=Issue with response to: '${question}'%0A%0AAnswer given:%0A${encodeURIComponent(impacts.message?.content || "")}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => console.log('Feedback logged:', question, impacts.message?.content)}
                >
                    Report any issue with this response if needed
                </a>
            </div>
        );
    };


    return (
        <Stack className={`${styles.answerContainer} ${isSelected && styles.selected}`} verticalAlign="space-between">
            <Stack.Item>
                <Stack horizontal horizontalAlign="space-between">
                    <AnswerIcon />
                    <div>
                        <IconButton
                            style={{ color: "black" }}
                            iconProps={{ iconName: "Lightbulb" }}
                            title="Show thought process"
                            ariaLabel="Show thought process"
                            onClick={() => onThoughtProcessClicked()}
                            disabled={!answer.context.thoughts?.length}
                        />
                    </div>
                </Stack>
            </Stack.Item>

            <Stack.Item grow>
                <div className={styles.answerText} dangerouslySetInnerHTML={{ __html: sanitizedAnswerHtml }}></div>
                
                <ImpactSummary question={answer.message.content} impacts={answer} />

            </Stack.Item>

            {!!parsedAnswer.citations.length && (
                <Stack.Item>
                    <Stack horizontal wrap tokens={{ childrenGap: 5 }}>
                        <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 5 }}>
                            <IconButton
                                iconProps={{ iconName: isReferencesCollapsed ? "ChevronDown" : "ChevronUp" }}
                                title={isReferencesCollapsed ? "Expand references" : "Collapse references"}
                                ariaLabel={isReferencesCollapsed ? "Expand references" : "Collapse references"}
                                onClick={() => setIsReferencesCollapsed(!isReferencesCollapsed)}
                            />
                            <span className={styles.citationLearnMore}>References:</span>
                        </Stack>
                    </Stack>
                    {!isReferencesCollapsed && (
                        <ol>
                            {parsedAnswer.citations.map((rowId, ind) => {
                                const citation = answer.context.data_points[rowId];
                                if (!citation) return null;
                                return (
                                    <li key={rowId}>
                                        <h4>{citation.content}</h4>
                                        <p className={styles.referenceMetadata}>URL: {citation.fileurl}</p>
                                        <p className={styles.referenceMetadata}>Page: {citation.pagenumber}</p>
                                    </li>
                                );
                            })}
                        </ol>
                    )}
                </Stack.Item>
            )}

            {!!followupQuestions?.length && showFollowupQuestions && onFollowupQuestionClicked && (
                <Stack.Item>
                    <Stack horizontal wrap className={`${!!parsedAnswer.citations.length ? styles.followupQuestionsList : ""}`} tokens={{ childrenGap: 6 }}>
                        <span className={styles.followupQuestionLearnMore}>Follow-up questions:</span>
                        {followupQuestions.map((x, i) => {
                            return (
                                <a key={i} className={styles.followupQuestion} title={x} onClick={() => onFollowupQuestionClicked(x)}>
                                    {`${x}`}
                                </a>
                            );
                        })}
                    </Stack>
                </Stack.Item>
            )}
        </Stack>
    );
};
