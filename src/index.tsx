import { definePlugin, call } from "@decky/api";
import { PanelSection, PanelSectionRow, ToggleField, staticClasses } from "@decky/ui";
import { FaMicrophoneSlash } from "react-icons/fa";
import { useState, useEffect, FC } from "react";

const Content: FC = () => {
    const [suppressionEnabled, setSuppressionEnabled] = useState(false);

    useEffect(() => {
        // Handle both boolean and object responses to prevent UI flicker
        call("get_suppression_state").then((res: any) => {
            if (typeof res === "boolean") setSuppressionEnabled(res);
            else if (res && typeof res === "object") setSuppressionEnabled(res.enabled === true);
        });
    }, []);

    return (
        <PanelSection title="Audio Processing">
            <PanelSectionRow>
                <ToggleField
                    label="Noise Suppression (RNNoise)"
                    description="Reduces background noise via LADSPA filter"
                    checked={suppressionEnabled}
                    onChange={(val) => {
                        setSuppressionEnabled(val);
                        call("toggle_suppression", val);
                    }}
                />
            </PanelSectionRow>
        </PanelSection>
    );
};

export default definePlugin(() => {
    return {
        name: "Lyftronics ANC",
        title: (
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                Lyftronics ANC
                <span style={{ fontSize: "0.8em", opacity: 0.7 }}>v1.0</span>
            </div>
        ),
        content: <Content />,
        icon: <FaMicrophoneSlash />,
    };
});
