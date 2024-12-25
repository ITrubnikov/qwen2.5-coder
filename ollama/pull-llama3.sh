
./bin/ollama serve &

pid=$!

sleep 5


echo "Pulling qwen2.5-coder:3b model"
ollama pull qwen2.5-coder:3b


wait $pid
