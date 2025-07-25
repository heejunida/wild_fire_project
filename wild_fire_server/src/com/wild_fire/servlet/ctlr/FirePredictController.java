package com.wild_fire.servlet.ctlr;

import java.io.*;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.ConcurrentHashMap;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@WebServlet("/fire-predict")
public class FirePredictController extends HttpServlet {

    public static final ConcurrentHashMap<String, Process> activeProcesses = new ConcurrentHashMap<>();
    public static final ConcurrentHashMap<String, JSONObject> resultStore = new ConcurrentHashMap<>(); // 예시: 결과 저장
    public static final ConcurrentHashMap<String, Boolean> cancellationStatus = new ConcurrentHashMap<>(); // New: To track cancellation status
    public static final ConcurrentHashMap<String, String> statusMessages = new ConcurrentHashMap<>(); // New: To track prediction status messages

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        System.out.println("\n--- New Fire Prediction Request Received ---");

        String lat = request.getParameter("lat");
        String lng = request.getParameter("lng");
        String fireDateStr = request.getParameter("fireDate");
        String fireTimeStr = request.getParameter("fireTime"); // --- NEW: Get the fire start time ---
        String requestId = request.getParameter("requestId"); // Get requestId from client

        if (requestId == null || requestId.isEmpty()) {
            response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            response.getWriter().write("{\"error\": \"Missing requestId parameter from client\"}");
            return;
        }

        // 1. 즉시 requestId만 응답 후 함수 종료!
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        out.write("{\"requestId\": \"" + requestId + "\"}");
        out.flush();
        out.close();


        // ---- 백그라운드에서 예측 파이프라인 실행 ----
        new Thread(() -> {
            JSONObject finalPrediction = new JSONObject(); // Initialize finalPrediction
            finalPrediction.put("status", "error"); // Default to error status
            finalPrediction.put("message", "Unknown error occurred.");

            try {
                if (lat == null || lng == null || fireDateStr == null) {
                    System.err.println("[FirePredict] Missing parameters");
                    finalPrediction.put("message", "Missing parameters.");
                    return; // Exit thread if parameters are missing
                }
                System.out.println("Parameters: lat=" + lat + ", lng=" + lng + ", fireDate=" + fireDateStr + ", requestId=" + requestId);

                DateTimeFormatter yyyymmddFormatter = DateTimeFormatter.ofPattern("yyyyMMdd");
                // --- FIX: The weather script now needs the fire's start date to fetch the *previous* day's weather ---
                LocalDate fireDate = LocalDate.parse(fireDateStr, yyyymmddFormatter);
                String startDate = fireDate.minusDays(1).format(yyyymmddFormatter); // 24 hours before
                String endDate = fireDate.format(yyyymmddFormatter); // The actual fire date
                String fireYear = String.valueOf(fireDate.getYear());

                // 2. Define script paths with the CORRECT project root
                String clientBasePath = "/Users/heejunida/wild_fire_project/wild_fire_client/";
                String weatherPy = clientBasePath + "auto_collection/fetch_all_weather.py";
                String demPy = clientBasePath + "auto_collection/land/fetch_land_merge.py";
                String ndviPy = clientBasePath + "auto_collection/forest_data/ndvi_modis.py";
                String treePy = clientBasePath + "auto_collection/forest_data/hgfc.py";
                String featEngPy = clientBasePath + "auto_collection/feature_engineering.py";
                String predPy = clientBasePath + "predict.py";

                try {
                    // --- Pipeline Step 1: Weather Data ---
                    statusMessages.put(requestId, "1/7: 기후 데이터 수집 중입니다.");
                    System.out.println("Step 1: Calling weather script: " + weatherPy);
                    // --- FIX: Pass the specific fire time to the weather script, fetching from the previous day up to the fire day ---
                    JSONObject weatherData = runPythonScript(requestId, weatherPy, lat, lng, startDate, endDate, fireTimeStr);
                    System.out.println("Weather script SUCCESS.");

                    // --- Pipeline Step 2: DEM Data ---
                    statusMessages.put(requestId, "2/7: 지형 데이터 수집 중입니다.");
                    System.out.println("Step 2: Calling DEM script: " + demPy);
                    JSONObject demData = runPythonScript(requestId, demPy, lat, lng);
                    System.out.println("DEM script SUCCESS.");

                    // --- Pipeline Step 3: NDVI Data ---
                    statusMessages.put(requestId, "3/7: NDVI 데이터 수집 중입니다.");
                    System.out.println("Step 3: Calling NDVI script: " + ndviPy);
                    JSONObject ndviData = runPythonScript(requestId, ndviPy, lat, lng, fireDateStr);
                    System.out.println("NDVI script SUCCESS.");

                    // --- Pipeline Step 4: Tree Cover Data ---
                    statusMessages.put(requestId, "4/7: 산림 피복 데이터 수집 중입니다.");
                    System.out.println("Step 4: Calling Tree Cover script: " + treePy);
                    JSONObject treeData = runPythonScript(requestId, treePy, lat, lng, fireYear);
                    System.out.println("Tree Cover script SUCCESS.");

                    // --- Pipeline Step 5: Merge Raw Features ---
                    statusMessages.put(requestId, "5/7: 원시 데이터 병합 중입니다.");
                    JSONObject rawFeatures = new JSONObject();
                    rawFeatures.putAll(weatherData);
                    rawFeatures.putAll(demData);
                    rawFeatures.putAll(ndviData);
                    rawFeatures.putAll(treeData);
                    System.out.println("Step 5: Merged all raw features.");

                    // --- Pipeline Step 6: Feature Engineering ---
                    statusMessages.put(requestId, "6/7: 특징 공학 처리 중입니다.");
                    System.out.println("Step 6: Calling Feature Engineering script: " + featEngPy);
                    JSONObject engineeredFeatures = runPythonScriptWithJsonInput(requestId, featEngPy, rawFeatures.toJSONString());
                    System.out.println("Feature Engineering SUCCESS.");

                    // --- Pipeline Step 7: Prediction ---
                    statusMessages.put(requestId, "7/7: 산불 확산 예측 중입니다.");
                    System.out.println("Step 7: Calling Prediction script: " + predPy);
                    finalPrediction = runPythonScriptWithJsonInput(requestId, predPy, engineeredFeatures.toJSONString());
                    System.out.println("Prediction SUCCESS. Final result: " + finalPrediction.toJSONString());

                } catch (Exception e) {
                    // Check if it was a cancellation based ONLY on cancellationStatus
                    if (FirePredictController.cancellationStatus.getOrDefault(requestId, false)) {
                        System.out.println("--- PIPELINE CANCELLED for requestId: " + requestId + " ---");
                        finalPrediction = new JSONObject();
                        finalPrediction.put("status", "cancelled");
                        statusMessages.put(requestId, "예측 취소됨.");
                    } else {
                        System.err.println("--- PIPELINE FAILED for requestId: " + requestId + " ---");
                        e.printStackTrace();
                        finalPrediction = new JSONObject();
                        finalPrediction.put("error", "Error during Python script execution: " + e.getMessage());
                        statusMessages.put(requestId, "예측 실패: " + e.getMessage());
                    }
                } finally {
                    // Clean up active process and cancellation status
                    activeProcesses.remove(requestId);
                    cancellationStatus.remove(requestId);
                    // Store the final prediction result (success, error, or cancelled)
                    resultStore.put(requestId, finalPrediction);
                    System.out.println("Result for requestId " + requestId + " stored: " + finalPrediction.toJSONString());
                    // Remove status message after result is stored
                    statusMessages.remove(requestId);
                }
            } catch (Exception e) {
                // Catch any exceptions from the outer try block (e.g., from runPythonScript itself)
                System.err.println("--- UNEXPECTED PIPELINE ERROR for requestId: " + requestId + " ---");
                e.printStackTrace();
                finalPrediction.put("error", "Unexpected error in pipeline: " + e.getMessage());
                resultStore.put(requestId, finalPrediction); // Ensure error is stored even for outer exceptions
                System.out.println("Error result for requestId " + requestId + " stored: " + finalPrediction.toJSONString());
                statusMessages.put(requestId, "예측 실패: 예상치 못한 오류.");
            }
        }).start();
    }

    // 만약 runPythonScript*, resultStore 사용을 위해 static이 필요하면 붙여주세요.
    private static JSONObject runPythonScript(String requestId, String pyPath, String... params) throws Exception {
        String[] cmd = new String[params.length + 2];
        cmd[0] = "python3";
        cmd[1] = pyPath;
        System.arraycopy(params, 0, cmd, 2, params.length);

        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.directory(new File("/Users/heejunida/wild_fire_project/wild_fire_client/"));
        pb.redirectErrorStream(true);
        Process process = pb.start();
        activeProcesses.put(requestId, process);

        StringBuilder sb = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append(System.lineSeparator());
            }
        }

        int exitCode = process.waitFor();
        String output = sb.toString().trim();

        if (exitCode != 0) {
            throw new Exception("Script '" + pyPath + "' failed with exit code " + exitCode + ". Full output:\n" + output);
        }

        try {
            int jsonStart = output.indexOf('{');
            if (jsonStart == -1) throw new Exception("No JSON object found in script output.");
            return (JSONObject) new JSONParser().parse(output.substring(jsonStart));
        } catch (Exception e) {
            throw new Exception("Script '" + pyPath + "' succeeded but produced invalid JSON. Full output:\n" + output);
        }
    }

    private static JSONObject runPythonScriptWithJsonInput(String requestId, String pyPath, String jsonInput) throws Exception {
        ProcessBuilder pb = new ProcessBuilder("python3", pyPath);
        pb.directory(new File("/Users/heejunida/wild_fire_project/wild_fire_client/"));
        pb.redirectErrorStream(true);
        Process process = pb.start();
        activeProcesses.put(requestId, process);

        try (BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(process.getOutputStream()))) {
            writer.write(jsonInput);
        }

        StringBuilder sb = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append(System.lineSeparator());
            }
        }

        int exitCode = process.waitFor();
        String output = sb.toString().trim();

        if (exitCode != 0) {
            throw new Exception("Script '" + pyPath + "' failed with exit code " + exitCode + ". Full output:\n" + output);
        }

        try {
            int jsonStart = output.indexOf('{');
            if (jsonStart == -1) throw new Exception("No JSON object found in script output.");
            return (JSONObject) new JSONParser().parse(output.substring(jsonStart));
        } catch (Exception e) {
            throw new Exception("Script '" + pyPath + "' succeeded but produced invalid JSON. Full output:\n" + output);
        }
    }

    // 결과 조회용 서블릿 (내부 static 클래스)
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
                // If result is null, it means prediction is still in progress
                // Include the current status message
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
}