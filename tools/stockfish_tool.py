import os
from stockfish import Stockfish
from pydantic import BaseModel, Field, validator
from typing import Literal, List, Dict, Any, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. 从环境变量加载 Stockfish 引擎路径
stockfish_path = os.getenv("STOCKFISH_PATH")
if not stockfish_path:
    raise ValueError("STOCKFISH_PATH not found in environment variables. Please set it in the .env file.")

if not os.path.exists(stockfish_path):
    raise FileNotFoundError(f"Stockfish executable not found at the specified path: {stockfish_path}")

# 2. 为不同的子功能定义输入模型以进行验证

class StockfishOptions(BaseModel):
    skill_level: int = Field(default=20, ge=0, le=20, description="Stockfish's skill level (0-20).")
    depth: int = Field(default=15, ge=1, le=30, description="Analysis depth (1-30). Higher is stronger but slower.")
    count: int = Field(default=3, ge=1, le=10, description="Number of top moves to return for 'get_top_moves' mode.")

class StockfishInput(BaseModel):
    mode: Literal['get_best_move', 'get_top_moves', 'evaluate_position'] = Field(
        description="The analysis mode to execute."
    )
    fen: str = Field(description="The FEN string of the current board position.")
    options: Optional[StockfishOptions] = Field(default_factory=StockfishOptions, description="Optional parameters for the analysis.")

    @validator('fen')
    def validate_fen_string(cls, v):
        # 简单的FEN格式校验，更严格的校验由Stockfish引擎自己完成
        parts = v.split()
        if len(parts) != 6:
            raise ValueError("FEN string must have 6 parts separated by spaces.")
        return v

# 3. 创建工具类
class StockfishTool:
    name = "stockfish_analyzer"
    description = (
        "A powerful chess analysis tool using the Stockfish engine. "
        "Use different modes to get the best move, top several moves, or a positional evaluation."
    )
    input_schema = StockfishInput

    async def execute(self, parameters: StockfishInput) -> dict:
        try:
            # --- 初始化 Stockfish 引擎 ---
            # 每次执行都创建一个新实例以保证状态纯净
            stockfish = Stockfish(
                path=stockfish_path,
                depth=parameters.options.depth,
                parameters={
                    "Threads": 2,  # 限制CPU使用，可根据服务器配置调整
                    "Skill Level": parameters.options.skill_level
                }
            )
            
            if not stockfish.is_fen_valid(parameters.fen):
                return {"success": False, "error": f"Invalid FEN string provided: {parameters.fen}"}
            
            stockfish.set_fen_position(parameters.fen)
            logger.info(f"Stockfish processing FEN: {parameters.fen} with mode: {parameters.mode}")

            # --- 根据 mode 执行功能 ---
            result = None
            if parameters.mode == 'get_best_move':
                best_move = stockfish.get_best_move()
                evaluation = stockfish.get_evaluation()
                result = {"best_move_uci": best_move, "evaluation": evaluation}
            
            elif parameters.mode == 'get_top_moves':
                top_moves = stockfish.get_top_moves(parameters.options.count)
                result = {"top_moves": top_moves}

            elif parameters.mode == 'evaluate_position':
                evaluation = stockfish.get_evaluation()
                result = {"evaluation": evaluation}
            
            logger.info(f"Stockfish execution successful. Result: {result}")
            return {"success": True, "data": result}

        except Exception as e:
            error_message = f"An error occurred in Stockfish tool: {str(e)}"
            logger.error(error_message)
            return {"success": False, "error": error_message}
