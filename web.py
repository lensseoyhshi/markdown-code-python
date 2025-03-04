from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import time
from typing import List, Dict
import uuid
import md_to_html
import asyncio

app = FastAPI()

# 添加CORS中间件以允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应设置为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保上传目录存在
UPLOAD_DIR = "D:\\md\\"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 存储任务进度的字典
task_progress: Dict[str, Dict] = {}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    上传单个文件
    """
    try:
        # 生成唯一文件名
        file_extension = file.filename
        basename, extension = os.path.splitext(file_extension)

        # 检查文件类型
        if extension.lower() not in ['.md', '.markdown']:
            raise HTTPException(status_code=400, detail="只接受Markdown文件(.md或.markdown)")

        # 创建唯一ID
        uuid_number = uuid.uuid4()
        task_id = str(uuid_number)

        # 初始化任务进度
        task_progress[task_id] = {
            "progress": 0,
            "status": "started",
            "out_path": "",
            "error": None
        }

        # 创建唯一的子目录
        uuid_dir = os.path.join(UPLOAD_DIR, task_id)
        input_dir = os.path.join(uuid_dir, "input")
        output_dir = os.path.join(uuid_dir, "out")

        # 确保目录存在
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # 构建完整的文件路径
        file_path = os.path.join(input_dir, file.filename)
        out_path = os.path.join(output_dir, f"{basename}.html")  # 改为.html扩展名

        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 在后台启动转换任务
        asyncio.create_task(process_markdown(file_path, out_path, task_id))

        # 立即返回任务ID
        return {"code": "200", "task_id": task_id, "out_path": out_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


async def process_markdown(file_path: str, out_path: str, task_id: str):
    """
    处理Markdown文件的后台任务
    """
    try:
        # 更新进度到25%
        task_progress[task_id]["progress"] = 25
        await asyncio.sleep(1)  # 模拟处理时间

        # 更新进度到50%
        task_progress[task_id]["progress"] = 50
        await asyncio.sleep(1)  # 模拟处理时间

        # 调用Markdown转HTML函数
        md_to_html.convert_md_to_html(file_path, out_path)

        # 更新进度到100%
        task_progress[task_id]["progress"] = 100
        task_progress[task_id]["status"] = "completed"
        task_progress[task_id]["out_path"] = out_path

        # 任务完成后保留状态30分钟，然后清除
        await asyncio.sleep(1800)
        if task_id in task_progress:
            del task_progress[task_id]

    except Exception as e:
        task_progress[task_id]["status"] = "failed"
        task_progress[task_id]["error"] = str(e)
        print(f"处理任务失败: {str(e)}")


@app.get("/upload-status")
async def task_status(request: Request):
    """
    提供任务状态的SSE端点
    """
    async def event_generator():
        # 发送初始消息
        yield f"data: {{\"progress\": 0, \"status\": \"connecting\"}}\n\n"

        task_id = request.query_params.get("task_id")
        if task_id and task_id in task_progress:
            # 如果提供了特定任务ID，则只返回该任务的进度
            last_progress = -1
            while True:
                task_data = task_progress.get(task_id, {})
                current_progress = task_data.get("progress", 0)

                # 只有在进度变化时才发送更新
                if current_progress != last_progress:
                    yield f"data: {task_data}\n\n"
                    last_progress = current_progress

                # 如果任务完成或失败，发送最终状态并结束
                if task_data.get("status") in ["completed", "failed"]:
                    yield f"data: {task_data}\n\n"
                    break

                await asyncio.sleep(0.5)
        else:
            # 如果没有提供任务ID或任务不存在，发送一些模拟进度
            for progress in [10, 30, 50, 70, 90, 100]:
                yield f"data: {{\"progress\": {progress}, \"status\": \"processing\"}}\n\n"
                await asyncio.sleep(1)

            yield f"data: {{\"progress\": 100, \"status\": \"completed\"}}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


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