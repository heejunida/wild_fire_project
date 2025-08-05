package com.wild_fire.servlet.ctlr;

import com.wild_fire.DAO.UserDAO;
import com.wild_fire.DAO.UserWildfirePredictionDAO;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import java.io.*;
import java.sql.Timestamp;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.*;

@WebServlet("/fire-predict")
public class FirePredictController extends HttpServlet {

    public static final ConcurrentHashMap<String, Process> activeProcesses = new ConcurrentHashMap<>();
    public static final ConcurrentHashMap<String, JSONObject> resultStore = new ConcurrentHashMap<>();
    public static final ConcurrentHashMap<String, Boolean> cancellationStatus = new ConcurrentHashMap<>();
    public static final ConcurrentHashMap<String, String> statusMessages = new ConcurrentHashMap<>();

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        System.out.println("\n--- New Fire Prediction Request Received ---");
        String userId = (String) request.getSession().getAttribute("user");
        if (userId == null) {
            response.getWriter().write("{\"error\":\"User not logged in\"}");
            return;
        }

        try {
            UserDAO userDao = new UserDAO();
            Long uId = userDao.getUidByUserId(userId);
            System.out.println("DEBUG: userId = " + userId + ", uId = " + uId + ", uId class = " + (uId != null ? uId.getClass().getName() : "null"));
            if (uId == null) {
                response.getWriter().write("{\"error\":\"User ID not found in DB\"}");
                return;
            }

            String lat = request.getParameter("lat");
            String lng = request.getParameter("lng");
            String fireDateStr = request.getParameter("fireDate");
            String fireTimeStr = request.getParameter("fireTime");
            String requestId = request.getParameter("requestId");

            if (requestId == null || requestId.isEmpty()) {
                response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
                response.getWriter().write("{\"error\": \"Missing requestId parameter from client\"}");
                return;
            }

            response.setContentType("application/json; charset=UTF-8");
            PrintWriter out = response.getWriter();
            out.write("{\"requestId\": \"" + requestId + "\"}");
            out.flush();
            out.close();

            new Thread(() -> {
                JSONObject finalResultJson = new JSONObject();
                finalResultJson.put("status", "error");
                finalResultJson.put("message", "Unknown error occurred.");

                try {
                    if (lat == null || lng == null || fireDateStr == null || fireTimeStr == null) {
                        throw new IllegalArgumentException("Missing required parameters (lat, lng, fireDate, fireTime).");
                    }
                    System.out.println("Parameters: lat=" + lat + ", lng=" + lng + ", fireDate=" + fireDateStr + ", fireTime=" + fireTimeStr + ", requestId=" + requestId);

                    DateTimeFormatter yyyyMMddFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
                    LocalDate fireDate = LocalDate.parse(fireDateStr, yyyyMMddFormatter);
                    String fireDateForScript = fireDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));

                    String clientBasePath = "/Users/heejunida/wild_fire_project/wild_fire_client/";
                    String weatherPy = clientBasePath + "auto_collection/fetch_all_weather.py";
                    String demPy = clientBasePath + "auto_collection/land/fetch_land_merge.py";
                    String ndviPy = clientBasePath + "auto_collection/forest_data/ndvi_modis.py";
                    String treePy = clientBasePath + "auto_collection/forest_data/hgfc.py";
                    String featEngPy = clientBasePath + "auto_collection/feature_engineering.py";
                    String predPy = clientBasePath + "predict_all.py";

                    // --- FIX: Parallel Data Collection ---
                    ExecutorService executor = Executors.newFixedThreadPool(4);
                    JSONObject weatherData, demData, ndviData, treeData;

                    try {
                        Future<JSONObject> weatherFuture = executor.submit(() -> {
                            statusMessages.put(requestId, "기후 데이터 수집 중...");
                            return runPythonScript(requestId, weatherPy, lat, lng, fireDateForScript, fireTimeStr.split(":")[0]);
                        });
                        Future<JSONObject> demFuture = executor.submit(() -> {
                            statusMessages.put(requestId, "지형 데이터 수집 중...");
                            return runPythonScript(requestId, demPy, lat, lng);
                        });
                        Future<JSONObject> ndviFuture = executor.submit(() -> {
                            statusMessages.put(requestId, "NDVI 데이터 수집 중...");
                            return runPythonScript(requestId, ndviPy, lat, lng, fireDateForScript);
                        });
                        Future<JSONObject> treeFuture = executor.submit(() -> {
                            statusMessages.put(requestId, "산림 피복 데이터 수집 중...");
                            return runPythonScript(requestId, treePy, lat, lng, String.valueOf(fireDate.getYear()));
                        });

                        // Retrieve results from futures
                        weatherData = weatherFuture.get();
                        demData = demFuture.get();
                        ndviData = ndviFuture.get();
                        treeData = treeFuture.get();

                    } finally {
                        executor.shutdownNow(); // Ensure executor is always shut down
                    }

                    statusMessages.put(requestId, "5 / 7: 원시 데이터 병합 중입니다.");
                    JSONObject rawFeatures = new JSONObject();
                    rawFeatures.putAll(weatherData);
                    rawFeatures.putAll(demData);
                    rawFeatures.putAll(ndviData);
                    rawFeatures.putAll(treeData);

                    // --- DEBUG: Print the JSON data being sent to the feature engineering script ---
                    System.out.println("DEBUG: JSON data for feature engineering:\n" + rawFeatures.toJSONString());

                    statusMessages.put(requestId, "6 / 7: 특징 공학 처리 중입니다.");
                    JSONObject engineeredFeatures = runPythonScriptWithJsonInput(requestId, featEngPy, rawFeatures.toJSONString());

                    // --- Prediction ---
                    statusMessages.put(requestId, "7 / 7: 산불 확산 예측 중입니다.");
                    finalResultJson = runPythonScriptWithJsonInput(requestId, predPy, engineeredFeatures.toJSONString());

                    // --- FIX: Load performance metrics and add them to the final JSON ---
                    if ("success".equals(finalResultJson.get("status"))) {
                        Map<String, Map<String, String>> performanceMetrics = loadPerformanceMetrics(clientBasePath + "model_performance_summary.csv");
                        finalResultJson.put("performance_metrics", performanceMetrics);
                    }

                    // --- Database Insertion ---
                    if (userId != null && "success".equals(finalResultJson.get("status"))) {
                        System.out.println("Attempting to save prediction to database for user: " + userId);
                        UserWildfirePredictionDAO dao = new UserWildfirePredictionDAO();
                        Map<String, Object> dbParams = new HashMap<>();
                        dbParams.put("U_ID", uId); // <-- FIX: Pass the numeric uId, not the string userId

                        LocalDateTime ldt = LocalDateTime.parse(fireDateStr + " " + fireTimeStr, DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm"));
                        dbParams.put("FIRE_DATETIME", Timestamp.valueOf(ldt));
                        dbParams.put("LATITUDE", Double.parseDouble(lat));
                        dbParams.put("LONGITUDE", Double.parseDouble(lng));
                        dbParams.put("FEATURES_JSON", engineeredFeatures.toJSONString());
                        dbParams.put("AREA_PRED", finalResultJson.get("area_pred_median")); // <-- FIX: Use the correct key for the median prediction
                        dbParams.put("FWI_PRED", finalResultJson.get("fwi_pred"));
                        dbParams.put("DIR_PRED", finalResultJson.get("dir_pred"));
                        dbParams.put("DISTANCE_PRED", finalResultJson.get("distance_pred"));

                        boolean success = dao.insertPrediction(dbParams);
                        if (success) {
                            System.out.println("Successfully inserted prediction into database.");
                        } else {
                            System.err.println("Failed to insert prediction into database.");
                        }
                    } else {
                        System.out.println("Skipping database insertion: User not logged in or prediction failed.");
                    }

                } catch (Exception e) {
                    if (cancellationStatus.getOrDefault(requestId, false)) {
                        finalResultJson.put("status", "cancelled");
                        statusMessages.put(requestId, "예측 취소됨.");
                    } else {
                        finalResultJson.put("error", "Error during pipeline execution: " + e.getMessage());
                        statusMessages.put(requestId, "예측 실패: " + e.getMessage());
                        e.printStackTrace();
                    }
                } finally {
                    activeProcesses.remove(requestId);
                    cancellationStatus.remove(requestId);
                    resultStore.put(requestId, finalResultJson);
                    statusMessages.remove(requestId);
                    System.out.println("Result for requestId " + requestId + " stored: " + finalResultJson.toJSONString());
                }
            }).start();
            System.out.println("Finished running pipeline execution with saving in database.");
        } catch (Exception ex) {
            ex.printStackTrace();
            response.getWriter().write("{\"error\":\"Internal server error\"}");
        }
    }

    private static JSONObject runPythonScript(String requestId, String pyPath, String... params) throws Exception {
        String pythonExecutable = "/opt/anaconda3/bin/python";
        // Construct the full command to be executed by the shell
        String command = pythonExecutable + " " + pyPath + " " + String.join(" ", params);

        ProcessBuilder pb = new ProcessBuilder("bash", "-c", command);
        pb.directory(new File("/Users/heejunida/wild_fire_project/wild_fire_client/"));
        Process process = pb.start();
        activeProcesses.put(requestId, process);

        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line);
            }
        }

        int exitCode = process.waitFor();
        if (exitCode != 0) {
            // Read stderr for more detailed error info
            StringBuilder errorOutput = new StringBuilder();
            try (BufferedReader errorReader = new BufferedReader(new InputStreamReader(process.getErrorStream()))) {
                String line;
                while ((line = errorReader.readLine()) != null) {
                    errorOutput.append(line).append("\n");
                }
            }
            throw new IOException("Script '" + pyPath + "' failed with exit code " + exitCode + ". Stderr: " + errorOutput.toString());
        }
        return (JSONObject) new JSONParser().parse(output.toString());
    }

    private static JSONObject runPythonScriptWithJsonInput(String requestId, String pyPath, String jsonInput) throws Exception {
        String pythonExecutable = "/opt/anaconda3/bin/python";
        String command = pythonExecutable + " " + pyPath;

        ProcessBuilder pb = new ProcessBuilder("bash", "-c", command);
        pb.directory(new File("/Users/heejunida/wild_fire_project/wild_fire_client/"));
        Process process = pb.start();
        activeProcesses.put(requestId, process);

        try (BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(process.getOutputStream()))) {
            writer.write(jsonInput);
        }

        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line);
            }
        }

        int exitCode = process.waitFor();
        if (exitCode != 0) {
            StringBuilder errorOutput = new StringBuilder();
            try (BufferedReader errorReader = new BufferedReader(new InputStreamReader(process.getErrorStream()))) {
                String line;
                while ((line = errorReader.readLine()) != null) {
                    errorOutput.append(line).append("\n");
                }
            }
            throw new IOException("Script '" + pyPath + "' failed with exit code " + exitCode + ". Stderr: " + errorOutput.toString());
        }
        return (JSONObject) new JSONParser().parse(output.toString());
    }
    
    @WebServlet("/fire-predict-result")
    public static class FirePredictResultServlet extends HttpServlet {
        @Override
        protected void doGet(HttpServletRequest request, HttpServletResponse response)
                throws ServletException, IOException {
            String requestId = request.getParameter("requestId");
            response.setContentType("application/json; charset=UTF-8");
            PrintWriter out = response.getWriter();
            JSONObject result = resultStore.get(requestId);
            if (result != null) {
                out.write(result.toJSONString());
            } else {
                JSONObject processingStatus = new JSONObject();
                processingStatus.put("status", "processing");
                String currentMessage = FirePredictController.statusMessages.get(requestId);
                if (currentMessage != null) {
                    processingStatus.put("message", currentMessage);
                }
                out.write(processingStatus.toJSONString());
            }
            out.flush();
            out.close();
        }
    }

    private static Map<String, Map<String, String>> loadPerformanceMetrics(String csvFilePath) {
        Map<String, Map<String, String>> metrics = new HashMap<>();
        try (BufferedReader br = new BufferedReader(new FileReader(csvFilePath))) {
            String line;
            String[] headers = null;
            boolean isFirstLine = true;
            while ((line = br.readLine()) != null) {
                if (isFirstLine) {
                    headers = line.split(",");
                    isFirstLine = false;
                    continue;
                }
                String[] values = line.split(",");
                String modelName = values[0];
                Map<String, String> modelMetrics = new HashMap<>();
                for (int i = 1; i < headers.length; i++) {
                    if (i < values.length && !values[i].isEmpty()) {
                        modelMetrics.put(headers[i], values[i]);
                    }
                }
                metrics.put(modelName, modelMetrics);
            }
        } catch (IOException e) {
            e.printStackTrace();
            // Return an empty map or handle the error as needed
        }
        return metrics;
    }
}