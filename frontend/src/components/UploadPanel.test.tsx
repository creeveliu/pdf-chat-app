import { fireEvent, render, screen } from "@testing-library/react";

import { UploadPanel } from "@/components/UploadPanel";

describe("UploadPanel", () => {
  it("accepts a dropped PDF and reports it through onFileChange", () => {
    const onFileChange = vi.fn();

    render(
      <UploadPanel
        fileName=""
        isUploading={false}
        uploadError={null}
        uploadResult={null}
        uploadStatus="还没有上传 PDF。"
        onFileChange={onFileChange}
        onUpload={vi.fn()}
      />,
    );

    const uploadCard = screen.getByText("选择 PDF 文件").closest("label");
    expect(uploadCard).not.toBeNull();

    const file = new File(["pdf"], "dropped-guide.pdf", { type: "application/pdf" });

    fireEvent.dragOver(uploadCard as HTMLElement, {
      dataTransfer: {
        files: [file],
        items: [{ kind: "file", type: "application/pdf", getAsFile: () => file }],
        types: ["Files"],
      },
    });

    fireEvent.drop(uploadCard as HTMLElement, {
      dataTransfer: {
        files: [file],
        items: [{ kind: "file", type: "application/pdf", getAsFile: () => file }],
        types: ["Files"],
      },
    });

    expect(onFileChange).toHaveBeenCalledWith(file);
  });
});
