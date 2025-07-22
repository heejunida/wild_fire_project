package com.wild_fire.servlet;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.*;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

@WebServlet("/fire-predict")
public class FirePredictController extends HttpServlet {
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        System.out.println("\n--- New Fire Prediction Request Received ---");

        // 1. Extract parameters
        String lat = request.getParameter("lat");
        String lng = request.getParameter("lng");
        String fireDateStr = request.getParameter("fireDate");
        if (lat == null || lng == null || fireDateStr == null) {
            response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            response.getWriter().write("{\"error\": \"Missing parameters\"}");
            return;
        }
        System.out.println("Parameters: lat=" + lat + ", lng=" + lng + ", fireDate=" + fireDateStr);

        DateTimeFormatter yyyyMMddFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        LocalDate fireDate = LocalDate.parse(fireDateStr, yyyyMMddFormatter);
        LocalDate weatherStartDate = fireDate.minusDays(1);
        DateTimeFormatter yyyymmddFormatter = DateTimeFormatter.ofPattern("yyyyMMdd");
        String startDate = weatherStartDate.format(yyyymmddFormatter);
        String endDate = fireDate.format(yyyymmddFormatter);
        String fireYear = String.valueOf(fireDate.getYear());

        // 2. Define script paths with the CORRECT project root
        String clientBasePath = "/Users/heejunida/wild_fire_project/wild_fire_client/";
        String weatherPy = clientBasePath + "auto_collection/fetch_all_weather.py";
        String demPy     = clientBasePath + "auto_collection/land/fetch_land_merge.py";
        String ndviPy    = clientBasePath + "auto_collection/forest_data/ndvi_modis.py";
        String treePy    = clientBasePath + "auto_collection/forest_data/hgfc.py";
        String featEngPy = clientBasePath + "auto_collection/feature_engineering.py";
        String predPy    = clientBasePath + "predict.py";

        JSONObject finalPrediction;

        try {
            // --- Pipeline Step 1: Weather Data ---
            System.out.println("Step 1: Calling weather script: " + weatherPy);
            JSONObject weatherData = runPythonScript(weatherPy, lat, lng, startDate, "0000", endDate, "2359");
            System.out.println("Weather script SUCCESS.");

            // --- Pipeline Step 2: DEM Data ---
            System.out.println("Step 2: Calling DEM script: " + demPy);
            JSONObject demData = runPythonScript(demPy, lat, lng);
            System.out.println("DEM script SUCCESS.");

            // --- Pipeline Step 3: NDVI Data ---
            System.out.println("Step 3: Calling NDVI script: " + ndviPy);
            JSONObject ndviData = runPythonScript(ndviPy, lat, lng, fireDateStr);
            System.out.println("NDVI script SUCCESS.");

            // --- Pipeline Step 4: Tree Cover Data ---
            System.out.println("Step 4: Calling Tree Cover script: " + treePy);
            JSONObject treeData = runPythonScript(treePy, lat, lng, fireYear);
            System.out.println("Tree Cover script SUCCESS.");

            // --- Pipeline Step 5: Merge Raw Features ---
            JSONObject rawFeatures = new JSONObject();
            rawFeatures.putAll(weatherData);
            rawFeatures.putAll(demData);
            rawFeatures.putAll(ndviData);
            rawFeatures.putAll(treeData);
            System.out.println("Step 5: Merged all raw features.");

            // --- Pipeline Step 6: Feature Engineering ---
            System.out.println("Step 6: Calling Feature Engineering script: " + featEngPy);
            JSONObject engineeredFeatures = runPythonScriptWithJsonInput(featEngPy, rawFeatures.toJSONString());
            System.out.println("Feature Engineering SUCCESS.");

            // --- Pipeline Step 7: Prediction ---
            System.out.println("Step 7: Calling Prediction script: " + predPy);
            finalPrediction = runPythonScriptWithJsonInput(predPy, engineeredFeatures.toJSONString());
            System.out.println("Prediction SUCCESS. Final result: " + finalPrediction.toJSONString());

        } catch (Exception e) {
            System.err.println("--- PIPELINE FAILED ---");
            e.printStackTrace(); // Print full stack trace to server console
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            response.getWriter().write("{\"error\": \"Error during Python script execution: " + e.getMessage() + "\"}");
            return;
        }

        // 4. Send the final prediction as the response
        response.setContentType("application/json; charset=UTF-8");
        PrintWriter out = response.getWriter();
        out.write(finalPrediction.toJSONString());
        out.flush();
        out.close();
    }

    private JSONObject runPythonScript(String pyPath, String... params) throws Exception {
        String[] cmd = new String[params.length + 2];
        cmd[0] = "python3";
        cmd[1] = pyPath;
        System.arraycopy(params, 0, cmd, 2, params.length);
        
        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.directory(new File("/Users/heejunida/wild_fire_project/wild_fire_client/"));
        pb.redirectErrorStream(true);
        Process process = pb.start();

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

    private JSONObject runPythonScriptWithJsonInput(String pyPath, String jsonInput) throws Exception {
        ProcessBuilder pb = new ProcessBuilder("python3", pyPath);
        pb.directory(new File("/Users/heejunida/wild_fire_project/wild_fire_client/"));
        pb.redirectErrorStream(true);
        Process process = pb.start();

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
}