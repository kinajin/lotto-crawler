const { connectDatabase } = require("./database");
const { addDataToDatabase } = require("./addData");

async function main() {
  try {
    // 데이터베이스 연결
    await connectDatabase();
    console.log("데이터베이스 연결 완료");

    // 데이터베이스에 데이터 추가
    await addDataToDatabase();
    console.log("데이터 추가 완료");
  } catch (error) {
    console.error("오류 발생:", error);
  } finally {
    // await sequelize.close();
    console.log("데이터베이스 연결 종료");
  }
}

main();
