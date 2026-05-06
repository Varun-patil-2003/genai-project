import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple
from langchain_openai import OpenAIEmbeddings

class VectorRepository:
    def __init__(self, index_path=None):
        return