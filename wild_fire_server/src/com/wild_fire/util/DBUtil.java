package com.wild_fire.util;

import java.io.InputStream;
import java.sql.*;
import java.util.Properties;

public class DBUtil {
    private static String dbDriver, dbUrl, dbUser, dbPassword;

    static {
        try (InputStream input = DBUtil.class.getClassLoader().getResourceAsStream("main/resources/db.properties")) {
            Properties prop = new Properties();
            prop.load(input);
            dbDriver = prop.getProperty("db.driver");
            dbUrl = prop.getProperty("db.url");
            dbUser = prop.getProperty("db.user");
            dbPassword = prop.getProperty("db.password");
            Class.forName(dbDriver);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static Connection getConnection() throws SQLException {
        return DriverManager.getConnection(dbUrl, dbUser, dbPassword);
    }
}
