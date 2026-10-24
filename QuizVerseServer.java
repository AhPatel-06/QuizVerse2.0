import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.Executors;

/**
 * Minimal Java backend starter for QuizVerse.
 * Provides a health endpoint and a demo score endpoint.
 */
public class QuizVerseServer {
    public static void main(String[] args) throws IOException {
        int port = args.length > 0 ? Integer.parseInt(args[0]) : 8080;
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/api/health", exchange -> respond(exchange, 200,
            "{\"status\":\"ok\",\"app\":\"QuizVerse\",\"backend\":\"Java\"}"));
        server.createContext("/api/score", exchange -> {
            if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
                respond(exchange, 405, "{\"error\":\"Use POST\"}");
                return;
            }
            String body = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            try {
                int correct = readNumber(body, "correct");
                int total = readNumber(body, "total");
                if (total <= 0 || correct < 0 || correct > total) {
                    respond(exchange, 400, "{\"error\":\"Invalid score values\"}");
                    return;
                }
                int percentage = Math.round(correct * 100.0f / total);
                respond(exchange, 200, "{\"correct\":" + correct + ",\"total\":" + total +
                    ",\"percentage\":" + percentage + "}");
            } catch (RuntimeException ex) {
                respond(exchange, 400, "{\"error\":\"Expected correct and total numbers\"}");
            }
        });
        server.setExecutor(Executors.newFixedThreadPool(4));
        server.start();
        System.out.println("QuizVerse Java API running at http://localhost:" + port);
    }

    private static int readNumber(String json, String key) {
        java.util.regex.Matcher m = java.util.regex.Pattern
            .compile("\"" + key + "\"\\s*:\\s*(\\d+)")
            .matcher(json);
        if (!m.find()) throw new IllegalArgumentException("Missing " + key);
        return Integer.parseInt(m.group(1));
    }

    private static void respond(HttpExchange exchange, int status, String body) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
        exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
        exchange.getResponseHeaders().set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
        exchange.getResponseHeaders().set("Access-Control-Allow-Headers", "Content-Type");
        exchange.sendResponseHeaders(status, bytes.length);
        try (var out = exchange.getResponseBody()) { out.write(bytes); }
    }
}