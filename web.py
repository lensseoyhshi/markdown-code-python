from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import shutil
import os
from typing import List
import uuid
import md_to_html

app = FastAPI()

# 确保上传目录存在
UPLOAD_DIR = "D:\\md\\"
os.makedirs(UPLOAD_DIR, exist_ok=True)
path_separator = os.sep

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    上传单个文件
    """

    try:
        # 生成唯一文件名
        # 生成唯一文件名
        file_extension = file.filename
        basename, extension = os.path.splitext(file_extension)
        uuid_number = uuid.uuid4()

        # 创建唯一的子目录
        uuid_dir = os.path.join(UPLOAD_DIR, str(uuid_number))
        input_dir = os.path.join(uuid_dir, "input")
        output_dir = os.path.join(uuid_dir, "out")

        # 确保目录存在
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # 构建完整的文件路径
        file_path = os.path.join(input_dir, file.filename)
        out_path = os.path.join(output_dir, f"{basename}.md")
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        md_to_html.convert_md_to_html(file_path, out_path)

        return {"code":"200","out_path":out_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@app.get("/get-file")
async def get_file(file_path: str):
    """
    根据文件全路径获取文件
    """
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        # 检查文件是否在允许的目录中（安全检查）
        if not file_path.startswith(UPLOAD_DIR):
            raise HTTPException(status_code=403, detail="无权访问该文件")

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/octet-stream"
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"获取文件失败: {str(e)}")



if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)